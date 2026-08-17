"""
Fixed-window rate limiting for plain Django views (DRF's own throttle
classes cover the API — the login endpoint this project needs limited is a
template view, not a DRF viewset). Backed by the shared Redis-based cache so
limits hold correctly across multiple worker processes, not just per-process.
"""
from functools import wraps

from django.core.cache import cache
from django.http import HttpResponse


def _client_identity(request) -> str:
    if request.user.is_authenticated:
        return f"user:{request.user.pk}"
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    ip = forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR", "unknown")
    return f"ip:{ip}"


def rate_limit(key_prefix: str, limit: int, period_seconds: int = 60):
    """Caps a view to `limit` requests per `period_seconds` per user/IP.

    Uses cache.add() + cache.incr() (not a plain set-with-refreshed-TTL) so
    the window is a true fixed window — a steady stream of requests can't
    dodge the limit by continually resetting the expiry.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            cache_key = f"ratelimit:{key_prefix}:{_client_identity(request)}"
            if cache.add(cache_key, 1, timeout=period_seconds):
                count = 1
            else:
                try:
                    count = cache.incr(cache_key)
                except ValueError:
                    # Key expired between add() and incr() — restart the window.
                    cache.set(cache_key, 1, timeout=period_seconds)
                    count = 1
            if count > limit:
                return HttpResponse("Too many requests. Please try again shortly.", status=429)
            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator
