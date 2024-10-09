import re
from functools import wraps
from flask import request, jsonify, current_app as app

from .db import *


USERNAME_REGEX = r'^[a-zA-Z0-9_]{3,20}$'  # alphanumeric username between 3 and 20 characters
PASSWORD_REGEX = r'^.{6,64}$'  # we have a strong password policy!


def validate_json_field_regex(field_name, pattern):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if request is JSON
            if not request.is_json:
                app.logger.info('  invalid request: json')
                return jsonify({"message": "Тело запроса должно быть в виде JSON"}), 400

            data = request.get_json()

            # Check if the field exists
            if field_name not in data:
                app.logger.info(f'  invalid request: missing field {field_name}')
                return jsonify({"message": f"'{field_name}' не указан"}), 400

            # Validate against regex pattern
            if not re.match(pattern, str(data[field_name])):
                app.logger.info(f'  invalid request: regex for {field_name} ({pattern})')
                return jsonify({"message": f"'{field_name}' должен соответствовать паттерну '{pattern}'"}), 400

            return f(*args, **kwargs)

        return decorated_function

    return decorator
