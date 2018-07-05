from celery import Celery
import os
#from simcore_sdk.config.rabbit import Config as rabbit_config

#rc = rabbit_config()
#celery = Celery(rc.name, broker=rc.broker, backend=rc.backend)

#celery.conf.update(
#  broker_heartbeat=1000.0,
#)

env = os.environ
RABBITMQ_USER = env.get('RABBITMQ_USER','simcore')
RABBITMQ_PASSWORD = env.get('RABBITMQ_PASSWORD','simcore')
RABBITMQ_LOG_CHANNEL = env.get('RABBITMQ_LOG_CHANNEL','comp.backend.channels.log')
RABBITMQ_PROGRESS_CHANNEL = env.get('RABBITMQ_PROGRESS_CHANNEL','comp.backend.channels.progress')
RABBITMQ_HOST="rabbit"
RABBITMQ_PORT=5672

AMQ_URL = 'amqp://{user}:{pw}@{url}:{port}'.format(user=RABBITMQ_USER, pw=RABBITMQ_PASSWORD, url=RABBITMQ_HOST, port=RABBITMQ_PORT)

CELERY_BROKER_URL = AMQ_URL
CELERY_RESULT_BACKEND=env.get('CELERY_RESULT_BACKEND','rpc://')


celery= Celery('tasks', broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
