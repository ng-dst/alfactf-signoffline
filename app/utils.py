import jwt
import json
import base64
import datetime
from random import SystemRandom
from functools import wraps
from flask import request, jsonify, current_app as app
from gmpy2 import next_prime

from .db import db


# Crypto params
size = 2048  # modulus size in bits
rounds = 16  # pool size for p,q is 2**rounds, so average attempt count is 2**(rounds//2) due to birthday paradox

rand = SystemRandom()
exp = rand.sample(range(32, size // 2 - 1), rounds)


def generate_rsa_key_pair():
    # FIXME  guys from CST complain on weak prng we use
    def generate_int():
        g = 2 ** (size//2 - 1)
        for i in range(rounds):
            g += 2 ** exp[i] * rand.randint(0, 1)
        return g

    def generate_prime():
        return int(next_prime(generate_int()))

    p = generate_prime()
    q = generate_prime()
    while p == q: q = generate_prime()
    
    n = p*q
    phi = (p-1)*(q-1)
    
    e = 65537
    d = pow(e, -1, phi)

    return (n, e), (p, q, d)


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('token')

        if not token:
            return jsonify({'message': 'Токен не найден в cookie'}), 401

        try:
            # decode jwt using user's corresponding pub key
            payload = token.split('.')[1] + '=='
            payload = json.loads(base64.urlsafe_b64decode(payload.encode('utf-8')))
            username = str(payload.get('user'))

            user = db.users.find_one({'username': username})
            if not user:
                # yet another enum
                app.logger.info(f'  unknown username {username} in token')
                return jsonify({'message': 'Пользователь не найден'}), 400

            payload = jwt.decode(token, user['public_key'], options={"require": ["exp", "iat"]}, algorithms=['RS256'])
            if payload.get('role') is None:
                app.logger.info(f'  role missing in token')
                return jsonify({'message': 'Не указана роль'}), 400

        except jwt.ExpiredSignatureError:
            app.logger.info(f'  token expired for user {username}')
            return jsonify({'message': 'Токен просрочен. Пожалуйста, войдите заново'}), 401
        except jwt.InvalidSignatureError:
            app.logger.info(f'  token signature is invalid for {username}')
            return jsonify({'message': 'Подпись JWT-токена не соответствует открытому ключу'}), 401
        except Exception:
            app.logger.info('  token is malformed or has incorrect format')
            return jsonify({'message': 'Некорректный формат токена'}), 400

        return f(payload, *args, **kwargs)

    return decorated


def create_jwt_token(user):
    token = jwt.encode({
        'user': user['username'],
        'iat': datetime.datetime.now(),
        'exp': datetime.datetime.now() + datetime.timedelta(hours=4),
        'role': user['role']
    }, user['private_key'], algorithm='RS256')
    return token
