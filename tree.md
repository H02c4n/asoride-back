asoride-back/
├── config/
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py              ← ortak ayarlar
│   │   ├── development.py       ← local (DEBUG, SQLite fallback)
│   │   └── production.py        ← Render (DEBUG=False)
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── apps/
│   ├── core/                    ← soyut model, pagination, permission, mixin
│   │   ├── models.py            ← BaseModel
│   │   ├── pagination.py
│   │   ├── permissions.py       ← IsCustomer, IsDriver, IsOwner
│   │   └── utils/
│   │       ├── geo.py           ← haversine, Point dönüşümleri
│   │       └── pricing.py       ← fiyat hesaplama (tek yer)
│   │
│   ├── users/
│   │   ├── models.py            ← User (role, location)
│   │   ├── serializers.py
│   │   ├── selectors.py         ← get_driver_by_username vb.
│   │   ├── services.py          ← register_user, update_location
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── permissions.py       ← IsDriver, IsCustomer
│   │
│   ├── rides/
│   │   ├── models.py            ← Ride, Rating
│   │   ├── serializers/
│   │   │   ├── __init__.py
│   │   │   ├── ride.py          ← RideSerializer (read)
│   │   │   ├── create.py        ← RideCreateSerializer
│   │   │   └── rating.py
│   │   ├── selectors.py         ← Ride.objects.filter(...).select_related
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── ride_service.py  ← accept_ride, update_status (state machine)
│   │   │   ├── stats_service.py ← driver_stats
│   │   │   └── rating_service.py
│   │   ├── views/
│   │   │   ├── __init__.py
│   │   │   ├── ride_viewset.py
│   │   │   ├── rating_viewset.py
│   │   │   └── stats_viewset.py
│   │   ├── consumers/
│   │   │   ├── __init__.py
│   │   │   └── ride_consumer.py ← WebSocket
│   │   ├── middleware.py        ← JWTAuthMiddleware
│   │   ├── routing.py
│   │   ├── kafka/
│   │   │   ├── producer.py
│   │   │   └── management/commands/run_consumer.py
│   │   ├── urls.py
│   │   └── tests/
│   │       ├── test_ride_service.py
│   │       └── test_views.py
│   │
│   └── notifications/
│       ├── models.py            ← PushSubscription
│       ├── services/
│       │   ├── push_service.py  ← send_push_to_user
│       │   └── ws_service.py    ← notify_ride_status (group_send)
│       ├── views.py
│       └── urls.py
│
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
├── Dockerfile
├── docker-compose.yml
├── manage.py
└── pytest.ini