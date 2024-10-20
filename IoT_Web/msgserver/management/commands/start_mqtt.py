from django.core.management.base import BaseCommand
from msgserver.MQTT_client import start_MQTT_client


class Command(BaseCommand):
    help = 'Starts the MQTT client'

    def handle(self, *args, **kwargs):
        start_MQTT_client()