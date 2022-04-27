import utils
import vm
import asyncio
import logging

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
def get_vms(cli_args):
    resource_client = ComputeManagementClient(cli_args.credential, cli_args.subscription_id)
    return resource_client.virtual_machine_scale_set_vms.list(
        cli_args.resource_group,
        cli_args.vmss_name
    )

@utils.Decorator()
def get(cli_args):
    resource_client = ComputeManagementClient(cli_args.credential, cli_args.subscription_id)
    return resource_client.virtual_machine_scale_sets.get(
        cli_args.resource_group,
        cli_args.vmss_name,
        'instanceView',
    )

@utils.Decorator()
def create(cli_args, subnet, store):
    resource_client = ComputeManagementClient(cli_args.credential, cli_args.subscription_id)
    create_async = resource_client.virtual_machine_scale_sets.begin_create_or_update(
        cli_args.resource_group,
        cli_args.vmss_name,
        {
            "location": cli_args.region,
            "sku": {
                "name": "Standard_B1ms",
                "tier": "Standard",
                "capacity": 100
            },
            "zones":[ "1"],
            "orchestrationMode": "Flexible",
            "platform_fault_domain_count": 1,
            "properties": {
                "virtualMachineProfile": {
                    "storageProfile": {
                        "imageReference": {
                            "sku": "18.04-LTS",
                            "publisher": "Canonical",
                            "version": "latest",
                            "offer": "UbuntuServer",
                        },
                    },
                    "os_disk": {
                        "caching": "ReadOnly",
                        "diffDiskSettings": {
                            "option": "Local"
                        },
                        "managedDisk": {
                            "storageAccountType": "Standard_LRS"
                        },
                        "createOption": "FromImage",
                    },
                    "diagnosticsProfile": {
                        "bootDiagnostics": {
                            "storageUri": f'{store.primary_endpoints.blob}',
                            "enabled": True,
                        }
                    },
                    "osProfile": {
                        "computerNamePrefix": "vmInstance",
                        "adminUsername": f'{cli_args.username}',
                        "adminPassword": "P4$$w0rdP4$$w0rd",
                        "linuxConfiguration": {
                            "ssh": {
                                "publicKeys": [
                                    {
                                        "path": "/home/azureUser/.ssh/authorized_keys",
                                        "keyData": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCq+96OV61LW/TU8BpJ67CvJ00rFktlAUd2uo94eABeKg4+52HKvrdGcbaEUFn2KnyMIKRbHShLvcCtGnOgNJpzClxI3PDPNWEP81jyNs1Tn9ay081mLpDvht5gdlSuHNUB78u2heGK07RvuYhoF4masYcKXdwjSg/Td+san6xDoSvVtST3YFjb3pnb7+DGgzeLqmPBBpr0fw5lmAjtqncrWcb7tbv2T9Ir8Qfc0NMNlDxdC4W54Jk1+FBXJUVAcaDuXqVUX6tLlihfsBubppwN9nxSJahoAaV8HXFUUHjoQEvlN/deAQvTOW8mLv1BZh3tNpMnQYWMt7qL9tSEe30nps+IV/ORRzGg9D4J/kIEnkxoWGe3fgloHaTzHoFwD262wfDIc2fWzlW3/jHLsSG+k7B3+T+mIVxXcsZthjAq57CmH5jHtZv0mmSBdZ9UpJjBcZ1qEhUtNo6pNlcSEJBLzn7wUU3+vRZ6qnQsytQXCA4Bn1/OPjdsPRjakn4c6h6L1qm/PXPlGKiID7uXCo9ZUyiXixTfu5rNgd+Tcsv3pqflUmAsKvJQMvhWeix/EttElOdKWoYcwmDv/Weo9wMFoMzArgP8VZxRIOa6CjK35EHTNINyP8Tz7fjHbnGJIDFiR2k/7n0QwXfSZ000cDI70Q4kuXaIXbqitt3k+rcvOQ=="
                                    }
                                ]
                            },
                        },
                    },
                    "upgradePolicy": {
                        "mode": "Manual"
                    },
                    "networkProfile": {
                        "networkApiVersion": "2020-11-01",
                        "networkInterfaceConfigurations": [{
                            "name": f'{cli_args.vmss_name}',
                            "properties": {
                                "primary": True,
                                "enableIPForwarding": True,
                                "ipConfigurations": [
                                    {
                                        "name": f'{cli_args.vmss_name}',
                                        "properties": {
                                            "subnet": {
                                                "id": f'{subnet.id}',
                                            },
                                            "publicIPAddressConfiguration": {
                                                "name": f'{cli_args.vmss_name}',
                                                "properties": {
                                                    "publicIPAddressVersion": "IPv4"
                                                },
                                            },
                                        }
                                    }
                                ],
                            }
                        }]
                    }
                },
            },
        }
    )
    create_async.wait()
    
    return create_async.result()


def get_or_create(args, store, first_subnet):
    try:
        vmss = get(args)
    except ResourceNotFoundError:
        vmss = create(args, first_subnet, store)

    return vmss

