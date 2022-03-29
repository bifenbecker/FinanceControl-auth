import datetime
import json
import stripe

from django.conf import settings
from django.http import HttpResponse
from rest_framework import status, serializers
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User, RefreshToken
from payments.models import (
    StripeCustomer,
    Subscription,
    Plan
)

from .serializers import UserSerializer, SettingsSerializer
from .utils import (
    gen_pair_tokens,
    verify_user,
    validate_data_for_user,
    all_methods_check_token,
    process_response
)


@all_methods_check_token
class UserViewSet(viewsets.ViewSet):

    def retrieve(self, request, *args, **kwargs):
        serializer = UserSerializer(kwargs['user'])
        return serializer.data, status.HTTP_200_OK, None

    def update(self, request, *args, **kwargs):
        user = kwargs['user']
        if user.is_active:
            try:
                validate_data_for_user(request.data)
                for key in request.data:
                    if key in dir(user):
                        user.__dict__[key] = request.data[key]

                user.save()
                serializer = UserSerializer(user)
                return serializer.data, status.HTTP_202_ACCEPTED, f'User was updated - {user.id}'

            except serializers.ValidationError as e:
                return {'msg': e.get_full_details()[0]['message']}, status.HTTP_304_NOT_MODIFIED, \
                       'Update user error. Validation error(1)'

            except Exception as e:
                return {'msg': str(e)}, status.HTTP_304_NOT_MODIFIED, 'Update user error.(2)'
        else:
            return {'msg': 'User was blocked'}, status.HTTP_423_LOCKED, 'Update user error. Block(2)'

    def destroy(self, request, *args, **kwargs):
        user = kwargs['user']
        id = user.id
        user.delete()
        return {'msg': 'User was deleted'}, status.HTTP_202_ACCEPTED, f'User - {id} was deleted'


class RegisterView(APIView):
    @process_response
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Add Free subscribe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        customers_api = stripe.Customer.list()['data']
        if user.email not in [customer['email'] for customer in customers_api]:
            customer_api = stripe.Customer.create(
                email=user.email,
                name=user.name
            )
        else:
            customer_api = stripe.Customer.retrieve(
                list(filter(lambda customer: customer['email'] == user.email, customers_api))[0]['id']
            )

        free_subscription = Subscription.objects.create(
            plan=None,
            sub_id=None
        )
        customer = StripeCustomer.objects.create(
            user=user,
            customer_id=customer_api['id'],
            subscription=free_subscription
        )
        user.save()

        return serializer.data, status.HTTP_201_CREATED, f'Register new user - id:{user.id} Username:{user.username}'


class LoginView(APIView):
    @process_response
    def post(self, request):
        email = request.data['email']
        password = request.data['password']

        response = Response()
        user = User.objects.filter(email=email).first()

        if user is None:
            return {
                       'email': 'User not found!'
                   }, status.HTTP_404_NOT_FOUND, None

        if not user.check_password(password):
            return {
                       'password': 'Incorrect password!'
                   }, status.HTTP_400_BAD_REQUEST, None

        verified_user, response.status_code = verify_user(user)

        if not verified_user:
            return {
                       'msg': 'No user'
                   }, status.HTTP_404_NOT_FOUND, None

        access_token, refresh_token = gen_pair_tokens(user)
        user.last_login = datetime.datetime.utcnow()
        user.save()

        return {
                   'access_token': access_token,
                   'refresh_token': refresh_token
               }, status.HTTP_200_OK, f'User - {user.id} logged'


def json_token(request):
    data = {
        "keys": [settings.KEY.export_public(as_dict=True)]
    }
    return HttpResponse(json.dumps(data))


class RefreshTokensView(APIView):
    @process_response
    def post(self, request):
        token = request.data.get('refresh_token', None)
        if not token:
            return 'Need send refresh token', status.HTTP_400_BAD_REQUEST, None

        refresh_token = RefreshToken.objects.filter(token=token).first()
        if refresh_token:
            user = refresh_token.user
            if refresh_token.is_valid():
                refresh_token.delete()
                access_token, refresh_token = gen_pair_tokens(user)
                return {
                           'access_token': access_token,
                           'refresh_token': refresh_token
                       }, status.HTTP_200_OK, None
            else:
                return 'No verify token', status.HTTP_403_FORBIDDEN, f'No verify token for user - {user.id}'
        else:
            return 'No such token', status.HTTP_400_BAD_REQUEST, 'No token'


class CurrencyList(APIView):

    @process_response
    def get(self, request):
        data = []
        for cur in settings.CURRENCY_CHOICES:
            data.append({'name': cur[0], 'char': cur[1]})

        return data, status.HTTP_200_OK, None


@all_methods_check_token
class UserSettingsView(viewsets.ViewSet):

    def get(self, request, *args, **kwargs):
        user = kwargs['user']
        user_settings_serializer = SettingsSerializer(instance=user.settings)
        return user_settings_serializer.data, status.HTTP_200_OK, None

    def update(self, request, *args, **kwargs):
        user = kwargs['user']
        user_settings = user.settings
        if 'currency' in request.data:
            cur = request.data['currency']
            try:
                user_settings.set_currency(cur)
            except Exception as e:
                return str(e), status.HTTP_400_BAD_REQUEST, f'User settings update error - {str(e)}(3)'

        user_settings_serializer = SettingsSerializer(instance=user_settings)
        access_token, refresh_token = gen_pair_tokens(user)
        result = user_settings_serializer.data
        result.update({'access_token': access_token, 'refresh_token': refresh_token})
        return result, status.HTTP_200_OK, f'Settings of user - {user.id} was updated'
