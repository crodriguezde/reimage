import utils
import json
import vm
import vmss
import logging
import asyncio
import backoff 

from azure.mgmt.compute.aio import ComputeManagementClient
from azure.core.exceptions import ResourceNotFoundError
from json import JSONDecodeError

@utils.Decorator()
async def _get(cli_args, vm):
    resource_client = ComputeManagementClient(cli_args.async_credential, cli_args.subscription_id)
    run_async = await resource_client.virtual_machines.begin_run_command(
        cli_args.resource_group,
        vm.name,
        {
            'command_id': 'RunShellScript',
            'script': [
                'curl -H Metadata:true --noproxy -s --url \"http://169.254.169.254/metadata/instance?api-version=2021-10-01\"'
            ]
        }
    )
    result = await run_async.result()
    message = result.value[0].message
    lines = message.split("\n")
    if len(lines[2]) > 0:
        try:
            imds = json.loads(lines[2])
            return imds
        except JSONDecodeError:
            return None
        
    return None


@backoff.on_predicate(backoff.expo, max_time=600)
def _wait_vm_state_running(args, vmss_vm):
    instance_vm = vm.get(args, vmss_vm)
    for status in instance_vm.statuses:
        if status.code == 'PowerState/running' and status.display_status == 'VM running':
            return instance_vm
    return None


@utils.Decorator()
def get_from_vmss_vms(args):
    loop = asyncio.get_event_loop()

    def signal_handler(signal, frame):
        loop.stop()

    signal.signal(signal.SIGINT, signal_handler)

    vmss_vms = vmss.get_vms(args)
    for vmss_vm in vmss_vms:
        instance_vm = _wait_vm_state_running(args, vmss_vm)
        asyncio.run(_get(args, vmss_vm))

