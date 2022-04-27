import utils 
from azure.mgmt.network import NetworkManagementClient
from azure.core.exceptions import ResourceNotFoundError

@utils.Decorator()
def get(cli_args):
    resource_client = NetworkManagementClient(cli_args.credential, cli_args.subscription_id)
    return resource_client.network_security_groups.get(
        cli_args.resource_group,
        cli_args.nsg_name,
    )

@utils.Decorator()
def create(cli_args):
    resource_client = NetworkManagementClient(cli_args.credential, cli_args.subscription_id)
    nsg_create = resource_client.network_security_groups.begin_create_or_update(
        cli_args.resource_group,
        cli_args.nsg_name,
        {
            "location": cli_args.region,
            "security_rules": [
                {
                    "name": "ssh_access",
                    "description": "port 22 access from internet",
                    "protocol": "Tcp",
                    "source_address_prefix": "Internet",
                    "source_port_range": "*",
                    "destination_port_range": "22",
                    "priority": 100,
                    "destination_address_prefix": "*",
                    "access": "Allow",
                    "direction": "Inbound"
                }
            ]
        }
    )
    nsg_create.wait()
    return nsg_create.result()

def get_or_create(args):
    try:
        nsg = get(args)
    except ResourceNotFoundError:
        nsg = create(args)
    return nsg