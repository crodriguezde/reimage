from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt.network import NetworkManagementClient
import utils

@utils.Decorator()
def create(cli_args, nsg):
    resource_client = NetworkManagementClient(cli_args.credential, cli_args.subscription_id)
    async_create = resource_client.virtual_networks.begin_create_or_update(
        cli_args.resource_group,
        cli_args.vnet_name, 
        {
            "addressSpace": {
                "addressPrefixes": [
                    "10.0.0.0/16"
                ],
            },
            "location": cli_args.region,
            "subnets": [
                {
                    "name": "default",
                    "address_prefix": "10.0.0.0/24",
                    "network_security_group": {
                        "id": nsg.id,
                    }
                }
            ]
        },
    )
    async_create.wait()

    return async_create.result()


@utils.Decorator()
def get(cli_args):
    resource_client = NetworkManagementClient(cli_args.credential, cli_args.subscription_id)
    return resource_client.virtual_networks.get(
        cli_args.resource_group,
        cli_args.vnet_name
        )

@utils.Decorator()
def subnets_list(cli_args):
    resource_client = NetworkManagementClient(cli_args.credential, cli_args.subscription_id)
    return resource_client.subnets.list(
        cli_args.resource_group,
         cli_args.vnet_name, 
    )

def get_or_create(args, nsg):
    try:
        vnet = get(args)
    except ResourceNotFoundError:
        vnet = create(args, nsg)

    return vnet

