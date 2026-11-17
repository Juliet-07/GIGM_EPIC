class DomainError(Exception):
    status_code = 400
    code = "domain_error"

    def __init__(self, message: str, **extra):
        super().__init__(message)
        self.message = message
        self.extra = extra


class NotFound(DomainError):
    status_code = 404
    code = "not_found"


class InvalidRoute(DomainError):
    """Origin == destination, or a zone pair with no fare defined."""
    status_code = 422
    code = "invalid_route"


class TripNotBookable(DomainError):
    """Trip is past 'scheduled', or its departure time has passed."""
    status_code = 409
    code = "trip_not_bookable"


class InsufficientSeats(DomainError):
    status_code = 409
    code = "insufficient_seats"


class InvalidTransition(DomainError):
    status_code = 409
    code = "invalid_transition"


class IdempotencyConflict(DomainError):
    """Same Idempotency-Key reused with a different request body."""
    status_code = 422
    code = "idempotency_key_reuse"