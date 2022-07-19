from datetime import datetime
import json
import pika
from pika.exceptions import AMQPConnectionError
import django
import os
import sys
import time
from attendees.models import AccountVO

sys.path.append("")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "attendees_bc.settings")
django.setup()


def update_accountvo(ch, method, properties, body):
    content = json.loads(body)
    first_name = content["first_name"]
    last_name = content["last_name"]
    email = content["email"]
    is_active = content["is_active"]
    updated_string = content["updated"]
    updated = datetime.fromisoformat(updated_string)

    if is_active:
        AccountVO.objects.filter(updated__lt=updated).update_or_create(
            email=email,
            defaults={
                "updated": updated,
                "first_name": first_name,
                "last_name": last_name,
            },
        )
    else:
        AccountVO.objects.filter(email=email).delete()


while True:
    try:
        parameters = pika.ConnectionParameters(host="rabbitmq")
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.exchange_declare(exchange="account_info", exchange_type="fanout")
        result = channel.queue_declare(queue="", exclusive=True)
        queue_name = result.method.queue

        channel.queue_bind(exchange="account_info", queue=queue_name)
        channel.basic_consume(
            queue=queue_name, on_message_callback=update_accountvo, auto_ack=True
        )
        channel.start_consuming()

    except AMQPConnectionError:
        print("Could not connect to RabbitMQ")
        time.sleep(2)
