
from azure.cli.core import get_default_cli
import subprocess

def azcli(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out,err = process.communicate()
    #print(out)
    exit_code = process.returncode
    if exit_code and exit_code != 0:
        print(err)
        sys.exit(exit_code)
    else:
        return out

def az_cli (args_str):
    temp = tempfile.TemporaryFile()
    args = args_str.split()
    code = get_default_cli().invoke(args, None, temp)
    temp.seek(0)
    data = temp.read().strip()
    temp.close()
    return [code, data]


@utils.Decorator()
def get(cli_args):
    resource_client = ContainerServiceClient(cli_args.credential, cli_args.subscription_id)
    try:
        result = resource_client.container_services.get(
                    cli_args.resource_group,
                    cli_args.aks_name,
                )
        return True
    except:
        return False

@utils.Decorator()
def delete(cli_args):
    resource_client = ContainerServiceClient(cli_args.credential, cli_args.subscription_id)
    delete_async = resource_client.container_services.begin_delete(
                    cli_args.resource_group,
                    cli_args.aks_name,
                )
    delete_async.wait()
    return delete_async.result()

@utils.Decorator()
def create(cli_args, hostgrp, msi_principal_id):
    # Hack, no sdk for ADH yet.
    cmd = ['az', 'aks', 'create','-g',f'{cli_args.resource_group}','-n',f'{cli_args.aks_name}',
                      '--location', f'{cli_args.region}', '--kubernetes-version', '1.23.3',
                      '--nodepool-name', 'agentpool1', '--node-count', f'{cli_args.num_nodes}',
                      '--host-group-id' ,f'{hostgrp.id}', '--node-vm-size', f'{cli_args.node_sku}',
                      '--enable-managed-identity', '--assign-identity', f'{msi_principal_id}',
                      '--zones', '1']
    print(' '.join(cmd))
    response = azcli(cmd)
    return response