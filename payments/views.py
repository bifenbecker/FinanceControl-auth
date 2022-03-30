import stripe
from stripe.error import InvalidRequestError
from django.conf import settings
from django.http.response import JsonResponse
from django.http import HttpResponse
from django.shortcuts import render
from rest_framework import viewsets
from rest_framework import status
from .models import StripeCustomer, Subscription, Plan
from user.utils import (
    gen_pair_tokens,
    verify_user,
    validate_data_for_user,
    all_methods_check_token,
    process_response
)


def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_PUBLIC_KEY}
        return JsonResponse(stripe_config, safe=False)


def success(request):
    return HttpResponse('Success')


def cancel(request):
    return HttpResponse('Failed')


@all_methods_check_token
class StripeViews(viewsets.ViewSet):

    def post(self, request, *args, **kwargs):
        user = kwargs['user']
        data = request.data
        stripe.api_key = settings.STRIPE_SECRET_KEY
        plan = Plan.objects.filter(name=data['name'], price=data['price']).first()
        if not plan:
            return {'msg': 'No such plan'}, status.HTTP_400_BAD_REQUEST, None

        if plan.name == 'Free' and not user.customer.subscription.sub_id:
            return {'msg': 'Current plan - Free'}, status.HTTP_400_BAD_REQUEST, None

        try:
            if not user.customer.subscription.sub_id:
                # First time create sub
                subscription_api = stripe.Subscription.create(
                    customer=user.customer.customer_id,
                    items=[
                        {
                            "price": plan.price_id,
                        },
                    ],
                    payment_behavior='default_incomplete',
                    expand=['latest_invoice.payment_intent'],
                )

                user.subscribe(plan, subscription_api.id)

                return {
                           'subscriptionId': subscription_api.id,
                           'clientSecret': subscription_api.latest_invoice.payment_intent.client_secret
                       }, status.HTTP_200_OK, None
            try:
                subscription_api = stripe.Subscription.retrieve(user.customer.subscription.sub_id)
            except InvalidRequestError:
                return {'msg': 'No such subscription'}, status.HTTP_400_BAD_REQUEST, None

            if data['name'] == 'Free':
                # Stop subscription
                stripe.Subscription.delete(
                    user.customer.subscription.sub_id
                )
                user.cancel_subscribe()

                return {'msg': 'Success. Current plan - Free'}, status.HTTP_200_OK, None
            else:
                # Change subscription
                stripe.Subscription.delete(
                    user.customer.subscription.sub_id,
                )

                new_subscription_api = stripe.Subscription.create(
                    customer=user.customer.customer_id,
                    items=[
                        {
                            "price": plan.price_id,
                        },
                    ],
                    payment_behavior='default_incomplete',
                    expand=['latest_invoice.payment_intent'],
                )
                user.subscribe(plan, new_subscription_api.id)

                return {
                    'subscriptionId': new_subscription_api.id,
                    'clientSecret': new_subscription_api.latest_invoice.payment_intent.client_secret
                }, status.HTTP_200_OK, None
        except Exception as e:
            return {'msg': str(e)}, status.HTTP_400_BAD_REQUEST, None
