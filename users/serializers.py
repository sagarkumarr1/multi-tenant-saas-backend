from rest_framework import serializers
from .models import User
from tenants.models import Tenant
class LoginSerializer(serializers.Serializer):
    username= serializers.CharField(max_length=100)
    password = serializers.CharField(write_only = True)
    

class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=200)
    password = serializers.CharField(write_only=True)
    tenant = serializers.PrimaryKeyRelatedField(
        queryset=Tenant.objects.all()
    )

    def create(self, validated_data):
        username = validated_data['username']
        password = validated_data['password']
        tenant = validated_data['tenant']

        user = User.objects.create_user(
            username=username,
            password=password
        )

        user.tenant = tenant
        user.save()

        return user