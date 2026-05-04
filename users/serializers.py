from rest_framework import serializers
from .models import User


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=100)
    password = serializers.CharField(write_only=True)


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=200)
    password = serializers.CharField(write_only=True)

    def create(self, validated_data):
        request = self.context['request']
        tenant = request.user.tenant
        
     
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )

        user.tenant = tenant
        user.created_by = request.user
        user.save()

        return user
    

class BulkUserActionSerializer(serializers.Serializer):
    user_ids = serializers.ListField(
        child=serializers.IntegerField()
    )