from azure.mgmt.compute import ComputeManagementClient
from azure.core.exceptions import ResourceNotFoundError

@utils.Decorator()
def create(cli_args):
    resource_client = ComputeManagementClient(cli_args.credential, cli_args.subscription_id)
    result = resource_client.dedicated_host_groups.create_or_update(
        cli_args.resource_group,
        cli_args.host_group,
        {
            'location': cli_args.region, 
            'zones': [
                cli_args.zone
            ],
            'platform_fault_domain_count': 5,
            'support_automatic_placement': True,
        }
    )
    return result

@utils.Decorator()
def get(cli_args):
    resource_client = ComputeManagementClient(cli_args.credential, cli_args.subscription_id)
    return resource_client.dedicated_host_groups.get(
        cli_args.resource_group,
        cli_args.host_group,
    )


@utils.Decorator()
def create_host(cli_args, idx):
    # TODO: ResourceExistsError 
    resource_client = ComputeManagementClient(cli_args.credential, cli_args.subscription_id)
    create_async = resource_client.dedicated_hosts.begin_create_or_update(
        cli_args.resource_group,
        cli_args.host_group,
        f'host{idx}-auto', 
        {
            'platform_fault_domain': int(idx),
            'sku': {
                'name': 'DSv3-Type3'
            },
            'location': cli_args.region,
        },
    )
    create_async.wait()
    return create_async.result()

