from types import SimpleNamespace as Town

import pytest

from app.errors import InvalidRoute
from app.fares import fare_cents, fare_for_towns

BRIEF = [  # (zone, zone, USD)
    (1, 1, 8), (1, 2, 18), (1, 3, 25), (1, 4, 35),
    (2, 2, 10), (2, 3, 18), (2, 4, 28),
    (3, 3, 8), (3, 4, 22), (4, 4, 8),
]


@pytest.mark.parametrize("a,b,usd", BRIEF)
def test_every_fare_from_the_brief(a, b, usd):
    assert fare_cents(a, b) == usd * 100


@pytest.mark.parametrize("a,b,usd", BRIEF)
def test_fares_are_symmetric(a, b, usd):
    assert fare_cents(b, a) == fare_cents(a, b) == usd * 100


def test_every_zone_pair_has_a_fare():
    for a in range(1, 5):
        for b in range(1, 5):
            assert fare_cents(a, b) > 0


def test_fare_is_integer_cents():
    assert isinstance(fare_cents(1, 4), int)


@pytest.mark.parametrize("a,b", [(0, 1), (1, 5), (5, 5), (-1, 2)])
def test_unknown_zone_is_rejected(a, b):
    with pytest.raises(InvalidRoute):
        fare_cents(a, b)


LAGOS, IBADAN = Town(id=1, name="Lagos", zone=1), Town(id=2, name="Ibadan", zone=1)
ENUGU, ONITSHA = Town(id=3, name="Enugu", zone=2), Town(id=4, name="Onitsha", zone=2)
ABUJA, KANO = Town(id=5, name="Abuja", zone=3), Town(id=6, name="Kano", zone=4)


@pytest.mark.parametrize("origin,dest,usd", [
    (LAGOS, IBADAN, 8),     # same zone, different towns
    (ENUGU, ONITSHA, 10),
    (LAGOS, KANO, 35),
    (KANO, LAGOS, 35),      # reverse direction
    (IBADAN, ONITSHA, 18),
    (ABUJA, KANO, 22),
    (ONITSHA, ABUJA, 18),
])
def test_town_to_town_pricing(origin, dest, usd):
    assert fare_for_towns(origin, dest) == usd * 100


@pytest.mark.parametrize("town", [LAGOS, KANO, ABUJA])
def test_same_town_is_not_a_journey(town):
    with pytest.raises(InvalidRoute):
        fare_for_towns(town, town)