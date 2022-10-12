import functools
from flask import request


def is_valid(api_key):
    return api_key == "ssss"


def api_required(func):
    @functools.wraps(func)
    def decorator(*args, **kwargs):
        if (
            request.headers
            and "X-Api-Key" in request.headers
            and request.headers["X-Api-Key"] == "SSSS"
        ):
            return func(*args, **kwargs)
        else:
            return {"msg": "Invalid API Key"}, 403

    return decorator
