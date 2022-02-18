from rest_framework import serializers
from rest_framework.utils.serializer_helpers import ReturnDict

from .models import User, Settings
from .utils import validate_data_for_user


class SettingsSerializer(serializers.ModelSerializer):
    currency = serializers.SerializerMethodField()

    class Meta:
        model = Settings
        fields = ('currency',)

    def get_currency(self, obj):
        return {'name': obj.currency, 'char': obj.get_currency_display()}


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

    def validate(self, attrs):
        try:
            validate_data_for_user(attrs)
            return attrs
        except serializers.ValidationError:
            raise serializers.ValidationError

    def get_user_settings(self, obj):
        selected_settings = Settings.objects.filter(user=obj).first()
        if selected_settings:
            return SettingsSerializer(selected_settings).data
        else:
            return {}

    @property
    def data(self):
        data = super(UserSerializer, self).data
        data.update({'settings': self.get_user_settings(self.instance)})
        del data['password']
        return ReturnDict(data, serializer=self)

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        instance = self.Meta.model(**validated_data)
        if password is not None:
            instance.set_password(password)
        instance.save()
        Settings.objects.create(
            user=instance
        )
        return instance
