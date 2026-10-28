"""
Kafka analytics consumer. Ride event'lerini dinler, loglar.
İleride: gerçek analytics (PostHog, Mixpanel), günlük raporlar, ML feature'ları.
"""
import json
import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from kafka import KafkaConsumer

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Ride event\'lerini dinleyip analytics toplar'

    def handle(self, *args, **options):
        cfg = {
            'bootstrap_servers': settings.KAFKA_BOOTSTRAP_SERVERS,
            'group_id': 'analytics-service',
            'value_deserializer': lambda m: json.loads(m.decode('utf-8')),
            'auto_offset_reset': 'earliest',
            'enable_auto_commit': True,
        }

        if settings.KAFKA_USERNAME and settings.KAFKA_PASSWORD:
            cfg.update({
                'security_protocol': 'SASL_SSL',
                'sasl_mechanism': 'SCRAM-SHA-256',
                'sasl_plain_username': settings.KAFKA_USERNAME,
                'sasl_plain_password': settings.KAFKA_PASSWORD,
            })
            if settings.KAFKA_CA_CERT:
                cfg['ssl_cafile'] = settings.KAFKA_CA_CERT

        consumer = KafkaConsumer(
            settings.KAFKA_TOPIC_RIDE_REQUESTED,
            settings.KAFKA_TOPIC_RIDE_STATUS,
            **cfg,
        )

        self.stdout.write(self.style.SUCCESS(
            f'[Analytics] Dinleniyor: {settings.KAFKA_BOOTSTRAP_SERVERS}'
        ))

        stats = {'requested': 0, 'status_changed': 0}

        try:
            for msg in consumer:
                data = msg.value
                event = data.get('event')

                if event == 'ride.requested':
                    stats['requested'] += 1
                    self.stdout.write(
                        f"[Analytics] Ride #{data['ride_id']} talep edildi "
                        f"(müşteri={data['customer_id']}, "
                        f"fiyat={data.get('price')} TL) | "
                        f"Toplam: {stats['requested']}"
                    )
                elif event == 'ride.status_changed':
                    stats['status_changed'] += 1
                    self.stdout.write(
                        f"[Analytics] Ride #{data['ride_id']} "
                        f"{data['old_status']} → {data['new_status']} | "
                        f"Toplam: {stats['status_changed']}"
                    )
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('[Analytics] Durduruluyor...'))
        finally:
            consumer.close()