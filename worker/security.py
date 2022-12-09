import functools
from flask import request

ADMIN_KEY = "dapperdan"
INTERNAL_KEY = "gnohzoaboudibahsaminoacnagijizey"
API_KEY = "SSSS"
INTERNAL_HEADERS = {"X-Api-Key": INTERNAL_KEY}


def api_required(func):
    """
    Wrapper that restricts endpoints to only be accessible by
    requests including the proper API key

    Inputs:
        func (callable) - the function to be wrapped
    """

    @functools.wraps(func)
    def decorator(*args, **kwargs):
        if request.headers and "X-Api-Key" in request.headers:
            secure_key = request.headers["X-Api-Key"]
            if secure_key in [API_KEY, INTERNAL_KEY, ADMIN_KEY]:
                return func(*args, **kwargs)
        return {"msg": "Invalid API Key"}, 403

    return decorator


def internal_required(func):
    """
    Wrapper that restricts endpoints to only be accessible by
    other nodes in the network

    Inputs:
        func (callable) - the function to be wrapped
    """

    @functools.wraps(func)
    def decorator(*args, **kwargs):
        if request.headers and "X-Api-Key" in request.headers:
            secure_key = request.headers["X-Api-Key"]
            if secure_key in [INTERNAL_KEY, ADMIN_KEY]:
                return func(*args, **kwargs)
        return {"msg": "Internal endpoint"}, 403

    return decorator


def admin_required(func):
    """
    Wrapper that restricts endpoints to only be accessible by
    requests including the proper API key

    Inputs:
        func (callable) - the function to be wrapped
    """

    @functools.wraps(func)
    def decorator(*args, **kwargs):
        if request.headers and "X-Api-Key" in request.headers:
            secure_key = request.headers["X-Api-Key"]
            if secure_key == ADMIN_KEY:
                return func(*args, **kwargs)
        return {"msg": "Admin endpoint"}, 403

    return decorator
