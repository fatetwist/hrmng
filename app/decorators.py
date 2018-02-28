# coding=utf-8
from functools import wraps
from flask import abort
from flask_login import current_user



def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.can(65535, 65535,65535):
            abort(403)
        return f(*args, **kwargs)
    return wrapper




# def permission_required(d,p,u):
#     def decorator(f):
#         @wraps(f)
#         def wrapper(*args, **kwargs):
#             if not current_user.can(d, p, u):
#                 abort(403)
#             return f(*args, **kwargs)
#         return wrapper
#     return decorator
