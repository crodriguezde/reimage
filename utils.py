import uuid
import logging
import time 
import datetime

class Decorator:
    def __init__(self):
        pass
    
    def __call__(self, fn):
        def timer(*args, **kwargs):
            start = time.time()
            result = fn(*args, **kwargs)
            end = time.time()
            log_print_time(f'[ {fn.__name__:<24} ] {result}', end-start)
            #print(f'{fn.__name__} {(end - start):.4f}s')
            return result
        return timer

UUID=uuid.uuid4()

def log_print(str):
    logging.info(str, extra={
        'custom_dimensions': {
            'uuid': f'{UUID}',
        }
    } )

def log_print_time(str, time):
    logging.info(str, extra={
        'custom_dimensions': {
            'uuid': f'{UUID}',
            'execution_time': f'{time}',
        }
    } )