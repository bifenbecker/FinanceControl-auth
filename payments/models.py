from django.db import models


class StripeCustomer(models.Model):
    user = models.OneToOneField('user.User', on_delete=models.CASCADE, related_name='customer')
    subscription = models.OneToOneField('Subscription', on_delete=models.PROTECT, related_name='customer')
    customer_id = models.CharField(max_length=128, verbose_name='ID')


class Plan(models.Model):
    name = models.CharField(max_length=64, verbose_name='Name', default=None)
    price_id = models.CharField(max_length=64, verbose_name='ID')
    currency = models.CharField(max_length=4, verbose_name='Currency')
    price = models.BigIntegerField(verbose_name='Price')  # cents
    interval = models.CharField(max_length=32, verbose_name='Interval')


class Subscription(models.Model):
    sub_id = models.CharField(max_length=64, verbose_name='ID', default=None, null=True)
    plan = models.OneToOneField(Plan, related_name='subscription', on_delete=models.CASCADE, default=None, null=True)

    def set_plan(self, new_plan: Plan):
        self.plan = new_plan
        self.save()