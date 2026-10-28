"""
Kafka producer (singleton). Uygulama yaşam döngüsü boyunca tek bağlantı.

- Lazy init: ilk `send` çağrısında oluşur.
- Local: PLAINTEXT (kafka:9092)
- Production (Aiven): SASL_SSL + SCRAM-SHA-256
"""
import json
import logging
import threading

from django.conf import settings
from kafka import KafkaProducer

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_producer: KafkaProducer | None = None


def _build_kafka_config() -> dict:
    cfg = {
        'bootstrap_servers': settings.KAFKA_BOOTSTRAP_SERVERS,
        'value_serializer': lambda v: json.dumps(v).encode('utf-8'),
        'acks': 'all',
        'retries': 3,
        'linger_ms': 10,
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

    return cfg


def get_producer() -> KafkaProducer:
    """Thread-safe singleton producer."""
    global _producer
    if _producer is None:
        with _lock:
            if _producer is None:
                _producer = KafkaProducer(**_build_kafka_config())
                logger.info('[Kafka] Producer başlatıldı')
    return _producer


def _send(topic: str, payload: dict) -> None:
    try:
        producer = get_producer()
        producer.send(topic, value=payload)
        logger.info(f'[Kafka] → {topic}: {payload.get("event")}')
    except Exception as e:
        logger.error(f'[Kafka] {topic} gönderilemedi: {e}')


# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------
def publish_ride_requested(ride) -> None:
    _send(settings.KAFKA_TOPIC_RIDE_REQUESTED, {
        'event': 'ride.requested',
        'ride_id': ride.id,
        'customer_id': ride.customer_id,
        'pickup_lat': ride.pickup_location.y,
        'pickup_lng': ride.pickup_location.x,
        'dropoff_lat': ride.dropoff_location.y,
        'dropoff_lng': ride.dropoff_location.x,
        'distance_km': float(ride.distance_km) if ride.distance_km else None,
        'price': float(ride.price) if ride.price else None,
    })


def publish_ride_status_changed(ride, old_status: str, new_status: str) -> None:
    _send(settings.KAFKA_TOPIC_RIDE_STATUS, {
        'event': 'ride.status_changed',
        'ride_id': ride.id,
        'customer_id': ride.customer_id,
        'driver_id': ride.driver_id,
        'old_status': old_status,
        'new_status': new_status,
    })