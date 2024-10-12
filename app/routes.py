from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from flask import Blueprint, render_template, make_response, send_file
from pymongo.errors import DuplicateKeyError

from .utils import *
from .validate import *
from .db import db

# Blueprint
main = Blueprint('main', __name__)


@main.before_request
def log_request_info():
    app.logger.info(f"{request.method} {request.path} HTTP/1.1")
    

@main.route('/api/auth/register', methods=['POST'])
@validate_json_field_regex('username', USERNAME_REGEX)
@validate_json_field_regex('password', PASSWORD_REGEX)
def api_register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = "user"

    # unsalted (who cares?)
    hashed_password = generate_password_hash(password)

    # Generate RSA key pair in a very secure way
    (n, e), (p, q, d) = generate_rsa_key_pair()

    public_numbers = rsa.RSAPublicNumbers(e, n)
    public_key = public_numbers.public_key(default_backend())

    private_numbers = rsa.RSAPrivateNumbers(p=p, q=q, d=d, dmp1=pow(e, -1, p-1), dmq1=pow(e, -1, q-1), iqmp=pow(q, -1, p), public_numbers=public_numbers)
    private_key = private_numbers.private_key(default_backend())

    # Serialize the private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )

    # Serialize the public key
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    user_data = {
        'username': username,
        'password': hashed_password,
        'role': role,
        'private_key': private_pem,
        'public_key': public_pem,
        'public_numbers': {
            'n': str(n),
            'e': str(e)
        }
    }

    try:
        db.users.insert_one(user_data)
    except DuplicateKeyError:
        app.logger.info(f'  attempt to register duplicate user {username}')
        return jsonify({'message': 'Пользователь уже существует'}), 409

    token = create_jwt_token(user_data)
    resp = make_response(jsonify({
                    'message': 'Вы успешно зарегистрировались!',
                    'role': role,
                    'username': username,
                    'token': token
                   }), 201)
    resp.set_cookie('token', token, samesite='Lax', max_age=3600)
    app.logger.info(f'  registered user {username}')
    return resp


@main.route('/api/auth/login', methods=['POST'])
@validate_json_field_regex('username', USERNAME_REGEX)
@validate_json_field_regex('password', PASSWORD_REGEX)
def api_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    # potential enumeration using timing but who cares
    user = db.users.find_one({'username': username})
    if user and check_password_hash(user['password'], password):
        token = create_jwt_token(user)
        resp = make_response(jsonify({'message': f'Вы вошли в систему как {username}',
                                      'token': token}), 200)
        resp.set_cookie('token', token, samesite='Lax', max_age=3600)
        app.logger.info(f'  user {username} logged in')
        return resp

    app.logger.info(f'  wrong login/password for {username}')
    return jsonify({'message': 'Неправильный логин или пароль'}), 401


@main.route('/api/jwt/verify', methods=['GET'])
@token_required
def api_verify_jwt(payload):
    username = payload['user']
    user = db.users.find_one({'username': username})
    resp = {'username': username, 'role': str(payload['role'])}
    if request.args.get('publicKey'):
        app.logger.info(f'  user {username} accessed his public key')
        resp['jwt_public_key'] = user['public_numbers']
    return jsonify(resp), 200


# frontend pages

def render_with_userdata(page, **kwargs):
    username = None
    role = None
    user, status = api_verify_jwt()
    if status == 200:
        username = user.json['username']
        role = user.json['role']
    return render_template(page, username=username, role=role, **kwargs)


@main.route('/')
def index():
    return render_with_userdata('index.html')


@main.route('/susurity')
def susurity():
    return render_with_userdata('susurity.html')


@main.route('/login')
def login():
    return render_with_userdata('login.html')


@main.route('/register')
def register():
    return render_with_userdata('register.html')


@main.route('/jwt-editor')
def jwt_editor():
    return render_with_userdata('jwt-editor.html')


@main.route('/admin')
@token_required
def admin(payload):
    if payload['role'] not in ('user', 'admin'):
        app.logger.info(f'  accessed /admin with invalid role {payload["role"]}')
        return jsonify({'message': 'Роль не найдена. Доступные роли: [user, admin]'}), 400
    if payload['role'] != 'admin':
        app.logger.info('  unauthorized access to /admin')
        return jsonify({'message': 'Страница доступна только администраторам'}), 403
    app.logger.info(f'  user {payload["user"]} has SOLVED the task!')
    return render_with_userdata('admin.html')


@main.route('/favicon.ico')
def favicon():
    return send_file('static/images/favicon.png', mimetype='image/png')


@main.route('/health')
def health():
    return '', 200


@main.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f'[!] An error occurred: {str(e)}')
    return jsonify({"message": "Ошибка при обработке запроса"}), 500
