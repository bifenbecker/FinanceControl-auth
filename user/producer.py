import pika
from django.conf import settings

credentials = pika.PlainCredentials('admin', 'admin')

params = pika.ConnectionParameters(settings.RABBITMQ_HOST, credentials=credentials)

connection = pika.BlockingConnection(params)

channel = connection.channel()


def logger(body, key='logger'):
    msg = f'Service: Auth - {body}'
    channel.basic_publish(exchange='',
                          routing_key=key,
                          body=msg)
