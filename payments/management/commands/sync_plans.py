import stripe
from django.core.management.base import BaseCommand
from django.conf import settings

from payments.models import Plan


class Command(BaseCommand):
    help = 'Syncronize plans'

    def handle(self, *args, **options):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        plans = stripe.Price.list(stripe.api_key, product=settings.STRIPE_PRODUCT_ID)
        for plan in plans['data']:
            id = plan['id']
            plan_db = Plan.objects.filter(price_id=id).first()
            if not plan_db:
                Plan.objects.create(
                    name=plan['nickname'],
                    currency=plan['currency'],
                    price_id=id,
                    interval=plan['recurring']['interval'],
                    price=plan['unit_amount']
                )