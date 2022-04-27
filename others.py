import utils

@utils.Decorator()
def accept_license(cli_args):
    resource_client = ConfluentManagementClient(cli_args.credential, cli_args.subscription_id)
    return resource_client.marketplace_agreements.create(
        {
            "publisher": "canonical",
            "product": "0001-com-ubuntu-server-focal",
            "plan": "20_04-lts-gen2",
            "accepted": True
        }
    )