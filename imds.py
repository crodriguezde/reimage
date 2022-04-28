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
from json import JSONDecodeError

async def _get(cli_args, queue):
    while True:
        instance_vm = await queue.get()
        logging.info(f'Starting processing for {instance_vm.name}')
        resource_client = ComputeManagementClient(cli_args.async_credential, cli_args.subscription_id)
        run_async = await resource_client.virtual_machines.begin_run_command(
            cli_args.resource_group,
            instance_vm.name,
            {
                'command_id': 'RunShellScript',
                'script': [
                    'curl -H Metadata:true --noproxy -s --url \"http://169.254.169.254/metadata/instance?api-version=2021-10-01\"'
                ]
            }
        )
        await run_async.wait()
        logging.info(f'finishin awaiting')
        result = await run_async.result()
        logging.ingo(f'Received result {result}')
        message = result.value[0].message
        lines = message.split("\n")
        if len(lines[2]) > 0:
            imds = json.loads(lines[2])
            logging.info(imds)
        queue.task_done()


@backoff.on_predicate(backoff.expo, max_time=600)
def _wait_vm_state_running(args, vmss_vm):
    instance_vm = vm.get(args, vmss_vm)
    for status in instance_vm.statuses:
        if status.code == 'PowerState/running' and status.display_status == 'VM running':
            return instance_vm
    return None


@utils.Decorator()
async def get_from_vmss_vms(args):
    queue = asyncio.Queue()

    # Create worker tasks
    tasks = []
    for i in range(10):
        task = asyncio.create_task(_get(args, queue))
        tasks.append(task)

    # Put work on the queue
    
    vmss_vms = vmss.get_vms(args)
    for vmss_vm in vmss_vms:
        instance_vm = _wait_vm_state_running(args, vmss_vm)
        queue.put_nowait(vm)
    logging.info(f'Finish getting all vms in vmss')

    await queue.join()

    # Cancel worker tasks
    for task in tasks:
        task.cancel()

    # Wait until all worker tasks are cancelled
    await asyncio.gather(*tasks, return_exceptions=True)

