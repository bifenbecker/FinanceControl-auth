import os

import pika

credentials = pika.PlainCredentials('admin', 'admin')
params = pika.ConnectionParameters(os.environ.get('RABBITMQ_HOST', 'localhost'), credentials=credentials)

connection = pika.BlockingConnection(params)

channel = connection.channel()

channel.queue_declare(queue='get_user')


def callback_get_user(ch, method, properties, body):
    print('GET DATA')
    print(body)


channel.basic_consume(queue='get_user',
                      auto_ack=True,
                      on_message_callback=callback_get_user)

channel.start_consuming()

channel.close()
