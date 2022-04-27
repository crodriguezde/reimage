

import utils
import backoff

from azure.mgmt.authorization import AuthorizationManagementClient
from azure.core.exceptions import ResourceNotFoundError

@backoff.on_exception(backoff.expo, HttpResponseError, max_time=300)
@utils.Decorator()
def assign_role_to_rg(cli_args, resource_group,  msi_principal_id):
    resource_client = AuthorizationManagementClient(cli_args.credential, cli_args.subscription_id, '2018-01-01-preview')
    # Get "Contributor" built-in role as a RoleDefinition object
    role_name = 'Contributor'
    roles = list(resource_client.role_definitions.list(
        resource_group.id,
        filter="roleName eq '{}'".format(role_name)
    ))
    assert len(roles) == 1
    contributor_role = roles[0]

    return resource_client.role_assignments.create(
        resource_group.id,
        uuid.uuid4(), # Role assignment random name
        {
                'role_definition_id': contributor_role.id,
                'principal_id': msi_principal_id,
                'principal_type': "ServicePrincipal", 
        }
    )


@utils.Decorator()
def get(cli_args):
    resource_client = ManagedServiceIdentityClient(cli_args.credential, cli_args.subscription_id)
    return resource_client.user_assigned_identities.get(
        cli_args.resource_group,
        cli_args.msi_name,
    )



@utils.Decorator()
def create(cli_args):
    resource_client = ManagedServiceIdentityClient(cli_args.credential, cli_args.subscription_id)
    return resource_client.user_assigned_identities.create_or_update(
        cli_args.resource_group,
        cli_args.msi_name,
        {
            "location": cli_args.region,
        }
    )


def get_or_create(args, nsg):
    try:
        msi = get(args)
    except ResourceNotFoundError:
        msi = create(args, nsg)

    return msi
