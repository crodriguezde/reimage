import utils

from azure.mgmt.compute import ComputeManagementClient
from azure.core.exceptions import ResourceNotFoundError

@utils.Decorator()
def run_command(cli_args, vm):
    resource_client = ComputeManagementClient(cli_args.credential, cli_args.subscription_id)
    async_run = resource_client.virtual_machine_run_commands.begin_create_or_update(
        cli_args.resource_group,
        vm.name, 
        'RunCommandName',
        {
            'location': cli_args.region,
            'parameters': [
                {
                    'name': 'curl',
                    'value': 'curl http://ifconfig.co'
                }
            ],
            'async_execution': True,
        }
    )
    async_run.wait()
    return async_run.result()


@utils.Decorator()
def get(cli_args, vm):
    resource_client = ComputeManagementClient(cli_args.credential, cli_args.subscription_id)
    return resource_client.virtual_machines.instance_view(
        cli_args.resource_group,
        vm.name
    )



