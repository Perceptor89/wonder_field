from .sender import send_request
import json
from wonder_fields.tasks import process_update
import logging


class Poller:
    def __init__(self):
        self.is_run: bool = False

    def poll(self):
        logging.info('Poller start')
        offset = 0
        while True:
            if not self.is_run:
                break
            params = {'offset': offset, 'timeout': 60}
            res = send_request('getUpdates', params)
            for u in res['result']:
                offset = u['update_id'] + 1
                process_update.delay(json.dumps(u))
        
        logging.info('Poller stop')
