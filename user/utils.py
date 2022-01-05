import datetime
import hashlib
import json
import random
import re
import string
import time
from typing import Union

from django.conf import settings
from jwcrypto import jwk, jwt
from rest_framework import status, serializers
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from .models import User, Settings
from .producer import logger
from exceptions import *


def verify_access_token(token: str) -> Union[dict, None]:
    """
    Check is valid access token
    """

    if not token:
        raise TokenNotFound("No token")

    try:
        key = settings.KEY
        # key = jwk.JWK(**settings.KEY)
        ET = jwt.JWT(key=key, jwt=token)
    except jwt.JWTExpired:
        raise Exception("Token expired")
    except Exception as e:
        raise e

    claims = json.loads(ET.claims)

    if claims['iss'] != settings.ISSUER:
        raise Exception("Incorrect issuer")

    return claims


def gen_pair_tokens(user):
    """
    Get access token and refresh token for user
    """
    user_settings = user.settings
    payload_for_access_token = {
        'id': user.id,
        'settings': user_settings.data,
        'exp': int(time.time()) + int(settings.JWT["ACCESS_TOKEN_LIFETIME"].seconds),
        'iat': int(time.time()),
        'iss': settings.ISSUER,
        'aud': settings.AUDIENCES
    }

    refresh_token = hashlib.md5(
        f'{user.id}{generate_random_string(settings.JWT["LENGTH_STRING_REFRESH_HASH"])}'.encode()).hexdigest()

    token = jwt.JWT(header={"alg": settings.JWT["ALGORITHM"], "type": "JWT"}, claims=payload_for_access_token)

    key = settings.KEY
    # key = jwk.JWK.generate(**settings.KEY)
    token.make_signed_token(key)
    access_token = token.serialize()

    user.update_refresh_token(refresh_token)

    return (access_token, refresh_token)


def validate_email(email: str) -> bool:
    """
    Check email
    :param email: str
    :return: True or False
    """

    pattern = r'[a-zA-Z0-9]+[@][a-z\.]+[a-z]{2,4}'
    if re.match(pattern, email):
        return True


def generate_random_string(length: int) -> str:
    """
    Generate random string
    :param length: Length of random string
    :return: string
    """
    letters = string.ascii_lowercase
    rand_string = ''.join(random.choice(letters) for _ in range(length))
    return rand_string


def verify_user(user: Union[int, User]):
    """
    Check status of user
    :params: user - User
    :return: status_code
    """
    if isinstance(user, int):
        user = User.objects.filter(id=user).first()

    if not user:
        return None, status.HTTP_404_NOT_FOUND
    elif not user.is_active:
        return user, status.HTTP_423_LOCKED

    return user, status.HTTP_200_OK


def validate_data_for_user(attrs):
    """

    """
    email = attrs.get('email')
    name = attrs.get('name')
    password = attrs.get('password')
    username = attrs.get('username')

    if User.objects.filter(email=email).exists():
        raise serializers.ValidationError('Email is already exist')

    if User.objects.filter(username=username).exists():
        raise serializers.ValidationError('Username is already exist')

    if name and len(name) < 4:
        raise serializers.ValidationError('Name is too short')

    if username and len(username) < 4:
        raise serializers.ValidationError('Username is too short')

    if password and len(password) < 4:
        raise serializers.ValidationError('Password is too easy')

    if email and not validate_email(email):
        raise serializers.ValidationError('Incorrect email')

    return True


def process_response(func):
    """
    Return data and status code
    :param func:
    :return:
    """

    def wrapper(*args, **kwargs):
        data, response_status_code, logger_msg = func(*args, **kwargs)
        if isinstance(data, str):
            data = {'msg': data}
        if logger_msg:
            try:
                logger(logger_msg)
            except:
                print("Message was not send")
        return Response(
            data=data,
            status=response_status_code
        )

    return wrapper


def check_token(func):
    def wrapper(request, *args, **kwargs):
        try:
            access_token = request.headers.get('jwt-assertion')
        except:
            return {'msg': "No token"}, status.HTTP_400_BAD_REQUEST, None

        try:
            claims = verify_access_token(access_token)
            kwargs.update({'claims': claims})
            user, status_code = verify_user(claims['id'])
            if status_code in [200, 423]:
                kwargs.update({'user': user})
                res, code, msg = func(request, *args, **kwargs)
                return res, code, msg
            else:
                return {'msg': "Error"}, status_code, None
        except Exception as e:
            return {'msg': str(e)}, status.HTTP_400_BAD_REQUEST, None

    return wrapper


def all_methods_check_token(cls):
    """
    Each method get payload from headers
    :param cls: Class
    :return: Class
    """

    class Cls(ViewSet):
        def __init__(self, *args, **kwargs):
            self._obj = cls(*args, **kwargs)

        def __getattribute__(self, item):
            try:
                x = super().__getattribute__(item)
            except:
                pass
            else:
                return x
            attr = self._obj.__getattribute__(item)
            if isinstance(attr, type(self.__init__)):
                return process_response(check_token(attr))
            else:
                return attr

    return Cls

