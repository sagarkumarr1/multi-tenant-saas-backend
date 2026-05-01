from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from .serializers import *


#For User Login 
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        user = authenticate(username=username, password=password)

        if user is None:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # JWT generate
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK
        )

class ProfileView(APIView):
    # 1. Ye line check karegi ki token valid hai ya nahi
    authentication_classes=[JWTAuthentication]
    # 2. Ye line check karegi ki user logged in hai ya nahi
    permission_classes=[IsAuthenticated]

    def get(self, request):
        user=request.user
         # safe tenant handling
        if user.tenant:
            tenant_name = user.tenant.organization_name
        else:
            tenant_name = "No Tenant"
        # Jab user authenticated hota hai, toh request.user mein user ka object mil jata hai
        content = {
            'message': f"Welcome {request.user.username}",
            'user': user.username,
            'tenant':tenant_name,
        }
        return Response(content)
    
#For User Registration
class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {"message": "User created successfully"},
            status=status.HTTP_201_CREATED
        )
    