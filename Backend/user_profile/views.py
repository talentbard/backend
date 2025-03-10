from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import UserProfile
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import (
    UserSignupSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    TokenRefreshSerializer
)
from .decorators import authenticate_user_session
from django.contrib.auth.hashers import make_password, check_password

HEADER_PARAMS = {
    'access_token': openapi.Parameter('accesstoken', openapi.IN_HEADER, description="local header param", type=openapi.IN_HEADER),
}

class UserSignupView(APIView):
    @swagger_auto_schema(
        operation_description="User signup endpoint with nested request body",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "auth_params": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Authentication-related parameters (optional)",
                    properties={
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                        "other_param": openapi.Schema(type=openapi.TYPE_STRING, description="Any other parameter"),
                    },
                ),
                "payload": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="User registration details",
                    properties={
                        "full_name": openapi.Schema(type=openapi.TYPE_STRING, description="Full name of the user"),
                        "email_id": openapi.Schema(type=openapi.TYPE_STRING, description="User email address"),
                        "phone_no": openapi.Schema(type=openapi.TYPE_STRING, description="Phone number (optional)"),
                        "role": openapi.Schema(type=openapi.TYPE_STRING, description="Role of the user"),
                        "password": openapi.Schema(type=openapi.TYPE_STRING, description="Password for the account"),
                        "admin_key": openapi.Schema(type=openapi.TYPE_STRING, description="admin key")
                    },
                    required=["full_name", "email_id", "password", "role","admin_key"],
                ),
            },
            required=["payload"],  # `payload` is required
        ),
        responses={
            201: openapi.Response(
                "User registered successfully",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING, description="Success message"),
                        "user_data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description="Serialized user data",
                            properties={
                                "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                                "full_name": openapi.Schema(type=openapi.TYPE_STRING, description="Full name"),
                                "email_id": openapi.Schema(type=openapi.TYPE_STRING, description="User email address"),
                                "phone_no": openapi.Schema(type=openapi.TYPE_STRING, description="Phone number"),
                                "added_date": openapi.Schema(type=openapi.FORMAT_DATETIME, description="Creation date"),
                            },
                        ),
                    },
                ),
            ),
            400: "Validation errors",
        },
    )
    def post(self, request):
        payload = request.data.get('payload', {})
        full_name = payload.get('full_name')
        email_id = payload.get('email_id')
        phone_no = payload.get('phone_no')
        role = payload.get('role')
        password = payload.get('password')
        admin_key = payload.get('admin_key')

        if not full_name or not email_id or not password:
            return Response(
                {"error": "Full name, email ID, and password are required in the payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if admin_key!="demo":
            return Response(
                {"error": "admin key incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = UserSignupSerializer(
            data={
                "full_name": full_name,
                "email_id": email_id,
                "phone_no": phone_no,
                "password": password,
                "role": role,
            }
        )
        if serializer.is_valid():
            user = serializer.save(password=make_password(serializer.validated_data['password']))

            user_data = {
                "user_id": str(user.user_id),
                "full_name": user.full_name,
                "email_id": user.email_id,
                "phone_no": user.phone_no,
                "added_date": user.added_date,
            }

            return Response(
                {"message": "User registered successfully", "user_data": user_data},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLoginView(APIView):
    @swagger_auto_schema(
        operation_description="User login endpoint with nested request body",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "auth_params": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Authentication-related parameters",
                    properties={
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                        "refresh_token": openapi.Schema(type=openapi.TYPE_STRING, description="Refresh token"),
                    },
                ),
                "payload": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="User login credentials",
                    properties={
                        "email": openapi.Schema(type=openapi.TYPE_STRING, description="User email"),
                        "role": openapi.Schema(type=openapi.TYPE_STRING, description="User role"),
                        "password": openapi.Schema(type=openapi.TYPE_STRING, description="User password"),
                        "is_freelancer": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="User type"),
                        
                    },
                    required=["email", "password", "is_freelancer"],
                ),
            },
            required=["payload"],  # Make `payload` required
        ),
        responses={
            200: openapi.Response(
                "Success",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "access_token": openapi.Schema(type=openapi.TYPE_STRING, description="JWT Access Token"),
                        "refresh_token": openapi.Schema(type=openapi.TYPE_STRING, description="JWT Refresh Token"),
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                    },
                ),
            ),
            400: "Bad Request",
            401: "Unauthorized",
        },
    )
    def post(self, request):
        payload = request.data.get('payload', {})
        email = payload.get('email')
        role = payload.get('role')
        password = payload.get('password')
        is_freelancer = payload.get('is_freelancer')


        if not email or not password:
            return Response(
                {"error": "Both email and password are required in the payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = UserLoginSerializer(data={"email_id": email, "password": password, "role": role})
        if serializer.is_valid():
            try:
                user = UserProfile.objects.get(email_id=serializer.validated_data['email_id'])

                if role==user.role and check_password(serializer.validated_data['password'], user.password):
                    refresh = RefreshToken.for_user(user)

                    return Response({
                        "access_token": str(refresh.access_token),
                        "refresh_token": str(refresh),
                        "user_id": str(user.user_id)
                    }, status=status.HTTP_200_OK)
                
                return Response({"error": "Invalid password"}, status=status.HTTP_401_UNAUTHORIZED)

            except UserProfile.DoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TokenRefreshView(APIView):
    @swagger_auto_schema(
        operation_description="Refresh an access token using the refresh token",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "auth_params": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Authentication-related parameters",
                    properties={
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                        "refresh_token": openapi.Schema(type=openapi.TYPE_STRING, description="Refresh token"),
                    },
                ),
                "payload": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Refresh token details",
                    properties={
                        "refresh_token": openapi.Schema(type=openapi.TYPE_STRING, description="Refresh token"),
                    },
                    required=["refresh_token"],
                ),
            },
            required=["payload"],  # `payload` is required
        ),
        responses={
            200: openapi.Response(
                "Access token refreshed successfully",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "access_token": openapi.Schema(type=openapi.TYPE_STRING, description="New Access Token"),
                    },
                ),
            ),
            400: "Invalid refresh token",
            401: "Unauthorized",
        },
    )
    def post(self, request):
        payload = request.data.get('payload', {})
        refresh_token = payload.get('refresh_token')

        if not refresh_token:
            return Response(
                {"error": "Refresh token is required in the payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            refresh = RefreshToken(refresh_token)
            return Response({"access_token": str(refresh.access_token)}, status=status.HTTP_200_OK)

        except Exception:
            return Response({"error": "Invalid or expired refresh token"}, status=status.HTTP_401_UNAUTHORIZED)


class UserProfileView(APIView):
    @swagger_auto_schema(
        operation_description="Retrieve the user's profile information using `auth_params`.",
        manual_parameters=[HEADER_PARAMS['access_token']],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "auth_params": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Authentication-related parameters",
                    properties={
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                        "refresh_token": openapi.Schema(type=openapi.TYPE_STRING, description="Refresh token"),
                    },
                    required=["user_id","refresh_token"],
                ),
            },
            required=["auth_params"],
        ),
        responses={
            200: openapi.Response(
                "Success",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                        "full_name": openapi.Schema(type=openapi.TYPE_STRING, description="Full name"),
                        "email_id": openapi.Schema(type=openapi.TYPE_STRING, description="User email address"),
                        "phone_no": openapi.Schema(type=openapi.TYPE_STRING, description="Phone number"),
                        "added_date": openapi.Schema(type=openapi.FORMAT_DATETIME, description="Creation date"),
                    },
                ),
            ),
            400: openapi.Response(
                "Bad Request",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING, description="Error message"),
                    },
                ),
            ),
            404: openapi.Response(
                "User Not Found",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING, description="Error message"),
                    },
                ),
            ),
            401: openapi.Response(
                "Unauthorized",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING, description="Error message"),
                    },
                ),
            ),
        },
    )
    @authenticate_user_session
    def post(self, request):
        # Extract the authenticated user from the request
        user = getattr(request, "user", None)
        

        if not user:
            return Response(
                {"error": "User is not authenticated."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Retrieve user profile
        try:
            user_profile = UserProfile.objects.get(user_id=user.user_id)
            serializer = UserProfileSerializer(user_profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
