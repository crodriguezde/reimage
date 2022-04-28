# Import the needed credential and management objects from the libraries.
import argparse
import logging

import time
import os
from logging import FileHandler
import asyncio

import nsg
import storage
import vmss
import vnet
import imds
import resource_groups


from azure.identity import AzureCliCredential
from azure.identity.aio import AzureCliCredential as AzureCliCredentialAsync
from azure.core.exceptions import HttpResponseError

from azure.core.exceptions import ClientAuthenticationError
from azure.identity._exceptions import CredentialUnavailableError
from opencensus.ext.azure.log_exporter import AzureLogHandler


def main():
    
    file_formatter = logging.Formatter('[ {asctime:s} {levelname:>8s} ] {message}', style='{', datefmt="%Y-%m-%dT%H:%M:%S")
    logger = logging.getLogger()

    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    file_logger_file_handler = FileHandler(f'./logs/{time.strftime("%Y%m%d-%H%M%S")}-log.txt')
    file_logger_file_handler.setLevel(logging.DEBUG)
    file_logger_file_handler.setFormatter(file_formatter)
    logger.addHandler(file_logger_file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(file_formatter)
    stream_handler.setLevel(logging.DEBUG)
    logger.addHandler(stream_handler)

    az_logger = logging.getLogger("azure.core.pipeline.policies.http_logging_policy")
    az_logger.setLevel(logging.WARNING)
    az_logger.addHandler(file_logger_file_handler)

    az_identity_logger = logging.getLogger("azure.identity._internal.decorators")
    az_identity_logger.setLevel(logging.WARNING)

    az_identity_logger = logging.getLogger("azure.identity._internal.aio.decorators")
    az_identity_logger.setLevel(logging.WARNING)

    url_logger = logging.getLogger("urllib3.connectionpool")
    url_logger.setLevel(logging.WARNING)

    application_insights = os.environ.get('APPLICATIONINSIGHTS_CONNECTION_STRING')
    try:
        azureLogHandler = AzureLogHandler()
        logger.addHandler(azureLogHandler)
        logging.info("logging to applications insights")
    except ValueError:
        pass

    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--resource_group', help='resource group name', default='VMSSReImageRun1')
    parser.add_argument('-r', '--region', help='region to deploy resources', default='southcentralus')
    parser.add_argument('-s', '--subscription_id', help='subscription id', default='') 
    parser.add_argument('-c', '--create', help='create initial resources - resource-group, vmss', action='store_true')
    parser.add_argument('-d', '--delete', help='delete resource group and exit', action='store_true')
    parser.add_argument('-v', '--vmss_name', help='Name of the vm scale set', default='vmssPeregrineTest')
    parser.add_argument('-i', '--instances', help='number of isntances to deploy, will be overprovisioned by 20%', default=100)
   
    
    args = parser.parse_args()

    try:
        # Acquire a credential object using CLI-based authentication.
        args.credential = AzureCliCredential()
        args.async_credential = AzureCliCredentialAsync()
    except ClientAuthenticationError:
        return
    
    if args.subscription_id == '':
        # Retrieve subscription ID from environment variable.
        args.subscription_id = os.environ['AZURE_SUBSCRIPTION_ID']

    # All names will be prepended with the region
    args.resource_group += args.region.upper()
    args.vnet_name = f'{args.vmss_name}-vnet'
    args.nsg_name = f'{args.vmss_name}-nsg'
    # Calculate number of instances with overprovision 
    args.instances = round(args.instances * 1.20)
    # TODO: Remove or change logic as this will result in a different storage account per run
    #id1 = str(uuid.uuid1())
    #first_eight=id1[:8]
    #args.storage_name = f'{args.vmss_name.lower()}{first_eight}'
    args.storage_name = 'vmsspipeline9fc2a6bc'

    args.username = f'azureUser'

    try:
        if args.delete:
            resource_groups.delete(args) 
            return

        if args.create and resource_groups.exists(args):
            resource_groups.delete(args)

        if not resource_groups.exists(args):
            resource_groups.create(args)

        rg = resource_groups.get(args)

        #accept_license(args)
        # Create VMSS 
        try:
            store = storage.get_or_create(args)

            nsg_obj = nsg.get_or_create(args)

            vnet_obj = vnet.get_or_create(args, nsg_obj)

            subnets = vnet.subnets_list(args)
            first_subnet = next(subnets)

            vmss_obj = vmss.get_or_create(args, store, first_subnet)

            vmss_vms = vmss.get_vms(args)
            
            asyncio.run(imds.get_from_vmss_vms(args))


        except HttpResponseError as ex:
            print(f'{ex}')
    except CredentialUnavailableError:
        return


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt: 
        logging.info('Exit per user request')
