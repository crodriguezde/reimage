import utils
from azure.mgmt.storage import StorageManagementClient
from azure.core.exceptions import ResourceNotFoundError

@utils.Decorator()
def get(cli_args):
    resource_client = StorageManagementClient(cli_args.credential, cli_args.subscription_id)
    return resource_client.storage_accounts.get_properties(
        cli_args.resource_group,
        f'{cli_args.resource_group}store'
    )


@utils.Decorator()
def create(cli_args):
    resource_client = StorageManagementClient(cli_args.credential, cli_args.subscription_id)
    create_async = resource_client.storage_accounts.begin_create(
       cli_args.resource_group,
       cli_args.storage_name,
        {
            "location": cli_args.region,
            "kind": "StorageV2",
            "sku": {
                "name": "Standard_LRS"
            }
        }
    )
    create_async.wait()

    return create_async.result()

@utils.Decorator()
def container_get(cli_args, store):
    resource_client = StorageManagementClient(cli_args.credential, cli_args.subscription_id)
    return resource_client.blob_containers.get(
        cli_args.resource_group,
        cli_args.storage_name,
        cli_args.container_name,
    )


@utils.Decorator()
def container_create(cli_args, store):
    resource_client = StorageManagementClient(cli_args.credential, cli_args.subscription_id)
    return resource_client.blob_containers.create(
        cli_args.resource_group,
        cli_args.storage_name,
        cli_args.container_name,
        {},
    )

def get_or_create(args):
    try:
        store = get(args)
    except ResourceNotFoundError:
        store = create(args)
    return store


