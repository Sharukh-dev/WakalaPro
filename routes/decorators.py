from functools import wraps

from flask import abort

from flask_login import current_user



def admin_required(function):


    @wraps(function)

    def wrapper(*args, **kwargs):


        if current_user.role != "admin":

            abort(403)


        return function(
            *args,
            **kwargs
        )


    return wrapper