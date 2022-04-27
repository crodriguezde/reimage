import utils
import os
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.confluent import ConfluentManagementClient

@utils.Decorator()
def get(cli_args):
    # Retrieve subscription ID from environment variable.
    subscription_id = os.environ['AZURE_SUBSCRIPTION_ID']

    # Obtain the management object for resources.
    resource_client = ResourceManagementClient(cli_args.credential, cli_args.subscription_id)

    # Provision the resource group.
    return resource_client.resource_groups.get(
       cli_args.resource_group,
    )


@utils.Decorator()
def exists(cli_args):
    # Obtain the management object for resources.
    resource_client = ResourceManagementClient(cli_args.credential, cli_args.subscription_id)

    # Provision the resource group.
    return resource_client.resource_groups.check_existence(
        cli_args.resource_group
    )


@utils.Decorator()
def delete(cli_args):
    # Obtain the management object for resources.
    resource_client = ResourceManagementClient(cli_args.credential, cli_args.subscription_id)
    # Provision the resource group.
    delete_async = resource_client.resource_groups.begin_delete(cli_args.resource_group)
    delete_async.wait()
    return delete_async.result()


@utils.Decorator()
def create(cli_args):
    # Retrieve subscription ID from environment variable.
    subscription_id = os.environ['AZURE_SUBSCRIPTION_ID']

    # Obtain the management object for resources.
    resource_client = ResourceManagementClient(cli_args.credential, cli_args.subscription_id)

    # Provision the resource group.
    return resource_client.resource_groups.create_or_update(
       cli_args.resource_group,
        {
            'location': cli_args.region
        }
    )

@utils.Decorator()
def role_assingment_check(cli_args, msi_principal_id):
    resource_client = AuthorizationManagementClient(cli_args.credential, cli_args.subscription_id)
    result = resource_client.role_assignments.list_for_resource_group(
        cli_args.resource_group,
    )
    for l in result:
       if l.properties.principal_id == msi_principal_id:
           return True 

    return False