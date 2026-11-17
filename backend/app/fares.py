from app.errors import InvalidRoute

# (lower_zone, higher_zone) -> USD
_BASE_FARE_USD: dict[tuple[int, int], int] = {
    (1, 1): 8,  (1, 2): 18, (1, 3): 25, (1, 4): 35,
    (2, 2): 10, (2, 3): 18, (2, 4): 28,
    (3, 3): 8,  (3, 4): 22,
    (4, 4): 8,
}


def fare_cents(zone_a: int, zone_b: int) -> int:
    key = (min(zone_a, zone_b), max(zone_a, zone_b))
    try:
        return _BASE_FARE_USD[key] * 100
    except KeyError:
        raise InvalidRoute(f"No fare defined between zone {zone_a} and zone {zone_b}") from None


def fare_for_towns(origin, destination) -> int:
    """`origin` / `destination` are Town-like (need .id, .name, .zone)."""
    if origin.id == destination.id:
        raise InvalidRoute("Origin and destination must be different towns")
    return fare_cents(origin.zone, destination.zone)