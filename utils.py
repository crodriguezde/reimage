import uuid
import logging
import time 
import datetime
import json

class Decorator:
    def __init__(self):
        pass
    
    def __call__(self, fn):
        def timer(*args, **kwargs):
            start = time.time()
            result = fn(*args, **kwargs)
            end = time.time()
            log_print_time(f'[ {fn.__name__:<24} ] {result}', end-start)
            return result
        return timer


def log_obj(imds):
    #print(f'DUMP: {imds}')
    logging.info('imds', extra={
        'custom_dimensions':{
            'platformFaultDomain': imds['compute']['platformFaultDomain'],
            'platformSubFaultDomain': imds['compute']['platformSubFaultDomain'],
            'platformUpdateDomain': imds['compute']['platformUpdateDomain'],
            'name': imds['compute']['name'],
            'location': imds['compute']['location'],
            'uuid': imds['uuid'],
            'zone': imds['compute']['zone'],
            'vmId': imds['compute']['vmId'],
            'vmScaleSetName': imds['compute']['vmScaleSetName']
        }
    })


def log_msg(msg):
    logging.info(msg)


def log_print_time(str, time):
    logging.info(str, extra={
        'custom_dimensions': {
            'execution_time': f'{time}',
        }
    } )