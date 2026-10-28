import math
from django.contrib.gis.geos import Point


# WGS84 (GPS koordinat sistemi)
SRID = 4326
EARTH_RADIUS_KM = 6371.0


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    İki koordinat arası mesafe (km) — Haversine formülü.
    PostGIS kullanmadan, sadece Python ile hesaplama.
    Frontend'deki `calculateDistance()` ile AYNI sonucu verir.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def make_point(lat: float, lng: float) -> Point:
    """(lat, lng) → PostGIS Point. DİKKAT: Point(x=lng, y=lat)."""
    return Point(lng, lat, srid=SRID)


def point_to_latlng(point: Point) -> dict:
    """PostGIS Point → {"lat": ..., "lng": ...}"""
    return {'lat': point.y, 'lng': point.x}


def distance_between_points(point1: Point, point2: Point) -> float:
    """İki PostGIS Point arası mesafe (km)."""
    return haversine_km(point1.y, point1.x, point2.y, point2.x)