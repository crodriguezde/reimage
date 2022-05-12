import utils
import json
import vm
import vmss
import backoff 
import asyncio
import logging
import random

from azure.mgmt.compute.aio import ComputeManagementClient
from azure.core.exceptions import ResourceNotFoundError
from azure.core.exceptions import ClientAuthenticationError 
from json import JSONDecodeError

finished = 0

async def report_progress(vm_queue, log_queue):
    while True:
        await asyncio.sleep(30)
        log_queue.put_nowait(f'VMs in vm_queue:{vm_queue.qsize()}')
        log_queue.put_nowait(f'VMs finish:{finished}')


async def increment_on_finish(finish_queue):
    global finished
    while True:
        i = await finish_queue.get()
        finished = finished + i



@backoff.on_exception(backoff.expo, FileNotFoundError, max_time=300)
def logger_retry(msg):
    if isinstance(msg, str):
        utils.log_msg(msg)
    elif isinstance(msg, dict):
        utils.log_obj(msg)


async def logging_worker(vm_queue):
    while True:
        msg = await vm_queue.get() 
        logger_retry(msg)
        vm_queue.task_done()


@backoff.on_exception(backoff.expo, FileNotFoundError, max_time=300)
async def _get(cli_args, vm_queue, log_queue, finish_queue):
    while True:
        vmss_vm = await vm_queue.get()
        instance_vm = _wait_vm_state_running(cli_args, vmss_vm)

        resource_client = ComputeManagementClient(cli_args.async_credential, cli_args.subscription_id)

        try:
            run_async = await resource_client.virtual_machines.begin_run_command(
                cli_args.resource_group,
                vmss_vm.name,
                {
                    'command_id': 'RunShellScript',
                    'script': [
                        'curl -H Metadata:true --noproxy -s --url \"http://169.254.169.254/metadata/instance?api-version=2021-10-01\"'
                    ]
                }
            )
        except ClientAuthenticationError:
            # Put vm back in case of failure for another worker to retry
            vm_queue.put_nowait(vmss_vm)
            vm_queue.task_done()
            continue
            
        await run_async.wait()

        result = await run_async.result()
        message = result.value[0].message
        lines = message.split("\n")
        if len(lines[2]) > 0:
            #lines[2] contains the message that we need
            imds = json.loads(lines[2])
             #Add uuid to the message
            imds['uuid'] = cli_args.uuid
            log_queue.put_nowait(imds)

        await resource_client.close()
        #resource_client._client.close()
        finish_queue.put_nowait(1)
        vm_queue.task_done()


@backoff.on_exception(backoff.expo,ClientAuthenticationError, max_time=600)
@backoff.on_predicate(backoff.expo, max_time=600)
def _wait_vm_state_running(args, vmss_vm):
    instance_vm = vm.get(args, vmss_vm)
    for status in instance_vm.statuses:
        if status.code == 'PowerState/running' and status.display_status == 'VM running':
            return instance_vm
    logging.info(f'vm {vmss_vm.name} not in ready state')
    return None


async def get_from_vmss_vms(args):
    vm_queue = asyncio.Queue()
    log_queue = asyncio.Queue()
    finish_queue = asyncio.Queue()

    log_tasks = [
        asyncio.create_task(logging_worker(log_queue)),
        asyncio.create_task(report_progress(vm_queue, log_queue)),
        asyncio.create_task(increment_on_finish(finish_queue))
    ]

    # Create worker tasks
    tasks = []
    for i in range(10):
        task = asyncio.create_task(_get(args, vm_queue, log_queue, finish_queue))
        tasks.append(task)

    # Put work on the vm_queue
    
    vmss_vms = vmss.get_vms(args)
    for vmss_vm in vmss_vms:
        vm_queue.put_nowait(vmss_vm)
    logging.info(f'Finish queuing all vms')

    await vm_queue.join()

    # Cancel worker tasks
    for task in tasks:
        task.cancel()

    log_tasks[0].cancel()
    log_tasks[1].cancel()
    log_tasks[2].cancel()
    # Wait until all worker tasks are cancelled
    await asyncio.gather(*tasks, return_exceptions=True)
    await asyncio.gather(*log_tasks, return_exceptions=True)

