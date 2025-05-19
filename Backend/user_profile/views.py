from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils import timezone
from datetime import datetime, timedelta
from .models import UserProfile, EmailOTP
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import (
    UserSignupSerializer,
    UserLoginSerializer,
    UserProfileSerializer,
    TokenRefreshSerializer
)
from talent.serializers import TalentRegistrationStatusSerializer
from .decorators import authenticate_user_session
from django.contrib.auth.hashers import make_password, check_password
import random
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

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
            serializer_talent = TalentRegistrationStatusSerializer(
            data={
                "user_id": user.user_id
            }
        )
            if serializer_talent.is_valid():
                serializer_talent.save()

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
                    },
                    required=["email", "password"],
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


#Google login view
class GoogleLoginSendOTP(APIView):
    """
    Handles Google login:
    - Accepts Google login payload (email, token, role)
    - Validates user
    - Sends OTP to email
    - Returns JWT tokens if valid
    """

    @swagger_auto_schema(
        operation_description="Google login - receive email and send OTP",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "auth_params": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Authentication-related parameters",
                    properties={
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                        "other_param": openapi.Schema(type=openapi.TYPE_STRING, description="Other optional parameter"),
                    },
                ),
                "payload": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Google login details",
                    properties={
                        "email": openapi.Schema(type=openapi.TYPE_STRING, description="User email"),                    },
                    required=["email"],
                ),
            },
            required=["payload"],
        ),
        responses={
            200: openapi.Response(
                "OTP sent successfully",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "access_token": openapi.Schema(type=openapi.TYPE_STRING),
                        "refresh_token": openapi.Schema(type=openapi.TYPE_STRING),
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: openapi.Response(
                "Email not provided or invalid",
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
    def post(self, request):
        payload = request.data.get('payload', {})
        email = payload.get('email')
        google_token = payload.get('google_token')

        if not email :
            return Response(
                {"error": "Both email are required in the payload."},
                status=status.HTTP_400_EMAIL_INVALID,
            )

        # TODO: Verify the google_token here with Google APIs if needed

        # Generate OTP
        otp = random.randint(100000, 999999)
        # Delete existing OTP for email (if any)
        EmailOTP.objects.filter(email=email).delete()

        # Save or update OTP in DB
        EmailOTP.objects.update_or_create(
            email=email,
            defaults={
                'otp': str(otp),
                'created_at': timezone.now()
            }
        )

        try:
            user = UserProfile.objects.get(email_id=email)

            # Send OTP email
            send_mail(
                subject="Your TalentBard OTP",
                message=f"Hello {user.full_name}, your OTP is: {otp}",
                from_email="noreply@talentbard.com",
                recipient_list=[email],
                fail_silently=False,
            )

            # Return JWT tokens (user is assumed registered and verified via Google)
            refresh = RefreshToken.for_user(user)

            return Response({
                "message": "OTP sent successfully to your email.",
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "user_id": str(user.user_id)
            }, status=status.HTTP_200_OK)

        except UserProfile.DoesNotExist:
            # User not registered: just send OTP
            send_mail(
                subject="Your TalentBard OTP",
                message=f"Hello, your OTP is: {otp}",
                from_email="noreply@talentbard.com",
                recipient_list=[email],
                fail_silently=False,
            )

            return Response({
                "message": "OTP sent successfully to your email. Proceed with registration."
            }, status=status.HTTP_200_OK)
        

#Verifying the OTP generated and sent to the email
class VerifyOTPView(APIView):
    """
    Verifies the OTP sent to user's email.
    If verified and user exists, returns tokens and user info.
    Otherwise, instructs to proceed with registration.
    """

    @swagger_auto_schema(
        operation_description="Verify OTP sent to user's email",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "payload": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="OTP verification details",
                    properties={
                        "email": openapi.Schema(type=openapi.TYPE_STRING, description="User email"),
                        "otp": openapi.Schema(type=openapi.TYPE_STRING, description="OTP received by user"),
                    },
                    required=["email", "otp"],
                )
            },
            required=["payload"],
        ),
        responses={
            200: openapi.Response(
                "OTP Verified",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING),
                        "access_token": openapi.Schema(type=openapi.TYPE_STRING),
                        "refresh_token": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: openapi.Response(
                "Invalid OTP or email",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            404: openapi.Response(
                "User not found",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
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
    def post(self, request):
        payload = request.data.get("payload", {})
        email = payload.get("email")
        otp = payload.get("otp")

        if not email or not otp:
            return Response(
                {"error": "Email and OTP are required in the payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            otp_record = EmailOTP.objects.get(email=email)

            if otp_record.is_expired():
                otp_record.delete()
                return Response({"error": "OTP has expired."}, status=status.HTTP_400_BAD_REQUEST)

            if otp_record.otp != str(otp):
                return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

            # Check expiry if needed
            if timezone.now() > otp_record.created_at + timedelta(minutes=5):
                return Response({"error": "OTP expired."}, status=status.HTTP_400_BAD_REQUEST)

            otp_record.delete()  # OTP used, delete it

        except EmailOTP.DoesNotExist:
            return Response({"error": "No OTP found for this email."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = UserProfile.objects.get(email_id=email)

            refresh = RefreshToken.for_user(user)

            return Response({
                "message": "OTP Verified Successfully.",
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "user_id": str(user.user_id)
            }, status=status.HTTP_200_OK)

        except UserProfile.DoesNotExist:
            return Response({
                "message": "OTP verified, but user does not exist. Please complete registration."
            }, status=status.HTTP_404_NOT_FOUND)