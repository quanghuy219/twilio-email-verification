from functools import wraps

from flask import request, jsonify

import verification
from main import db, app
from models.user import User
from libs import jwttoken


def parse_args(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        request_args = request.get_json() or {}
        if request.method == 'GET':
            request_args = request.args.to_dict()

        kwargs['args'] = request_args
        return f(*args, **kwargs)

    return decorated_function


def access_token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        authorization = None
        if 'Authorization' in request.headers:
            authorization = request.headers['Authorization']

        if not authorization or not authorization.startswith('Bearer '):
            error = {
                'message': 'Invalid authorization header'
            }
            return jsonify(error), 400

        # Decode the token which has been passed in the request headers
        token = jwttoken.decode(authorization[len('Bearer '):])

        account = User.query.filter_by(id=token['sub']).one_or_none()

        if not account:
            return jsonify({'message': 'Unauthorized'}), 403

        kwargs['user'] = account
        return f(*args, **kwargs)

    return decorated_function


@app.route('/signup/email', methods=['POST'])
@parse_args
def signup_by_email(args):
    email = args.get('email')
    password = args.get('password')
    if not (email and password):
        return {'message': 'Email and password are required'}

    user = User.query.filter_by(email=email).first()
    if user is not None:
        return {'message': 'User already exists'}, 400

    user = User(
        email=email,
        password=password,
        email_verified=False
    )
    db.session.add(user)
    db.session.commit()
    verification.send_verification_email(user.email)
    access_token = jwttoken.encode(user)
    data = {
        'message': 'Your account has been created. Check your email and complete sign-up process',
        'access_token': access_token
    }
    return data


@app.route('/login/email', methods=['POST'])
@parse_args
def login_by_email(args):
    email = args.get('email')
    password = args.get('password')
    if not (email and password):
        return {'message': 'Email and password are required'}

    user = User.query.filter_by(email=email).first()
    if not user or user.password != password:
        return {'message': 'Email or password is incorrect'}, 400

    access_token = jwttoken.encode(user)
    data = {
        'access_token': access_token,
        'id': user.id,
        'email': user.email,
        'email_verified': user.email_verified
    }
    return data


@app.route('/verify/email', methods=['POST'])
@parse_args
@access_token_required
def verify_email(args, user):
    code = args['code']

    if user.email_verified:
        return {'message': 'Your email has been verified'}, 400

    if verification.verify_email(user.email, code):
        user.email_verified = True
        db.session.commit()
        return {'message': 'Congratulations! Your account has been activated'}

    return {'message': 'Something wrong happened when verifying your email'}, 400


@app.route('/verify/resend-email', methods=['GET'])
@access_token_required
def resend_verification_email(user):
    verification.send_verification_email(user.email)
    return {'message': 'New email has been sent to your mailbox'}
