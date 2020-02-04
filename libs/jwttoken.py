import datetime

import jwt

from config import config


def encode(account):
    iat = datetime.datetime.utcnow()
    return jwt.encode({
        'sub': account.id,
        'iat': iat,
        'exp': iat + datetime.timedelta(days=365),
    }, config.JWT_SECRET).decode()


def decode(access_token):
    try:
        token = jwt.decode(access_token, config.JWT_SECRET, leeway=10, algorithms="HS256")
    except jwt.InvalidTokenError:
        return None
    return token
