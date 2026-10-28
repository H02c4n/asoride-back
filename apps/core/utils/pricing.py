from .geo import haversine_km, distance_between_points


# -------------------------------------------------------------------
# Fiyatlandırma Sabitleri (TEK GERÇEĞİN KAYNAĞI)
# Frontend'deki `constants.ts` ile AYNI değerleri taşımalı!
# -------------------------------------------------------------------
BASE_FARE = 30.00        # Açılış ücreti (TL)
PER_KM_RATE = 15.00      # Kilometre başı (TL)
MIN_FARE = 40.00         # Minimum ücret


def calculate_price_from_coords(
    pickup_lat: float,
    pickup_lng: float,
    dropoff_lat: float,
    dropoff_lng: float,
) -> dict:
    """
    Koordinatlardan fiyat ve mesafe hesapla.

    Returns:
        {
            'distance_km': float,   # mesafe (km, 2 ondalık)
            'price': float,         # toplam ücret (TL, 2 ondalık)
        }
    """
    distance_km = haversine_km(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng)
    return calculate_price_from_distance(distance_km)


def calculate_price_from_points(pickup_point, dropoff_point) -> dict:
    """PostGIS Point objelerinden fiyat hesapla."""
    distance_km = distance_between_points(pickup_point, dropoff_point)
    return calculate_price_from_distance(distance_km)


def calculate_price_from_distance(distance_km: float) -> dict:
    """Hesaplanmış mesafeden fiyat döndür."""
    price = BASE_FARE + (distance_km * PER_KM_RATE)
    price = max(price, MIN_FARE)  # minimum ücret koruması

    return {
        'distance_km': round(distance_km, 2),
        'price': round(price, 2),
    }