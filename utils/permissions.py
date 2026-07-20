from functools import wraps

from flask import abort

from flask_login import current_user





def role_required(*roles):

    def decorator(function):

        @wraps(function)
        def wrapper(*args, **kwargs):


            # User not logged in
            if not current_user.is_authenticated:

                abort(401)



            # User role not allowed
            if current_user.role not in roles:

                abort(403)



            return function(*args, **kwargs)


        return wrapper


    return decorator