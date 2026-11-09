from app.ratelimit import RateLimiter


def test_limits_per_key_and_recovers():
    now = [0.0]
    limiter = RateLimiter(2, per_seconds=60, clock=lambda: now[0])
    assert limiter.allow("a") and limiter.allow("a")
    assert not limiter.allow("a")
    assert limiter.allow("b")          # other clients unaffected
    now[0] = 61
    assert limiter.allow("a")          # window slid


def test_zero_disables_limiting():
    limiter = RateLimiter(0)
    assert all(limiter.allow("x") for _ in range(1000))
