import os

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')


broker_url = f'redis://{REDIS_HOST}:{REDIS_PORT}/'
# result_backend = f'redis://{REDIS_HOST}:{REDIS_PORT}/'
task_track_started = True
include = [
    'wonder_fields.tasks',
]
