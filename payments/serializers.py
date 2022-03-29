from rest_framework import serializers
from rest_framework.utils.serializer_helpers import ReturnDict

from .models import Subscription, Plan


class PlanSerializer(serializers.ModelSerializer):

    class Meta:
        model = Plan
        fields = (
            'name',
            'price',
            'currency'
        )


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = ('plan', )

    def get_plan(self, obj):
        if obj.plan:
            return PlanSerializer(obj.plan).data
        else:
            return {
                'name': 'Free',
                'price': 0.0
            }
