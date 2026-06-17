from functools import wraps
from flask import redirect, url_for
from flask_login import current_user


def admin_required(f):
    from app.models import Admin

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not isinstance(current_user, Admin):
            return redirect(url_for('user_bp.index'))
        return f(*args, **kwargs)
    return decorated_function
