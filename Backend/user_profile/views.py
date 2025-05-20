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
import random, re
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
    - Accepts Google login payload (email, google_token)
    - Validates Google token and user
    - Sends OTP to email
    - Returns JWT tokens if valid
    """

    @swagger_auto_schema(
        operation_description="Google login - receive email and Google token, validate, and send OTP",
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
                        "email": openapi.Schema(type=openapi.TYPE_STRING, description="User email"),
                    },
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
                    },
                ),
            ),
            400: openapi.Response(
                "Email  not provided or invalid",
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
            404: openapi.Response(
                "User Not Found",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING, description="Error message"),
                    },
                ),
            ),
            500: openapi.Response(
                "Server Error",
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

        # Validate email presence
        if not email:
            return Response(
                {"error": "Email are required in the payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validate email format
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, email):
            return Response(
                {"error": "Invalid email format."},
                status=status.HTTP_400_BAD_REQUEST,
            )


        # Generate OTP
        otp = random.randint(100000, 999999)

        # Delete existing OTP for email (if any)
        try:
            EmailOTP.objects.filter(email=email).delete()
        except Exception as e:
            return Response(
                {"error": f"Failed to clear previous OTP: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Save or update OTP in DB
        try:
            EmailOTP.objects.update_or_create(
                email=email,
                defaults={
                    'otp': str(otp),
                    'created_at': timezone.now()
                }
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to save OTP: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Send OTP email
        try:
            subject = "Your TalentBard OTP for Account Verification"
            message = f"""
Dear Talent,

Thank you for choosing TalentBard! To proceed with your account verification, please use the following One-Time Password (OTP):

Your OTP: {otp}

This OTP is valid for the next 10 minutes. Please enter it in the verification field to complete the process. If you did not request this OTP, please ignore this email or contact our support team at support@talentbard.com.

We’re excited to have you on board!

Best regards,
The TalentBard Team
"""
            html_message = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
        }}
        .container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            text-align: center;
            padding: 20px 0;
            background-color: #00A3E0;
            color: #ffffff;
            border-radius: 8px 8px 0 0;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
        }}
        .content {{
            padding: 20px;
            line-height: 1.6;
            color: #333333;
        }}
        .otp {{
            font-size: 24px;
            font-weight: bold;
            color: #00A3E0;
            text-align: center;
            margin: 20px 0;
        }}
        .footer {{
            text-align: center;
            padding: 10px;
            font-size: 12px;
            color: #777777;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to TalentBard</h1>
        </div>
        <div class="content">
            <p>Dear Talent,</p>
            <p>Thank you for choosing TalentBard! To verify your account, please use the following One-Time Password (OTP):</p>
            <div class="otp">{otp}</div>
            <p>This OTP is valid for the next 5 minutes. Please enter it in the verification field to complete the process.</p>
            <p>If you did not request this OTP, please ignore this email or contact our support team at <a href="mailto:support@talentbard.com">support@talentbard.com</a>.</p>
            <p>We’re excited to have you on board and look forward to helping you showcase your talent!</p>
            <p>Best regards,<br>The TalentBard Team</p>
        </div>
        <div class="footer">
            <p>© 2025 TalentBard. All rights reserved.</p>
            <p>Need help? Contact us at <a href="mailto:support@talentbard.com">support@talentbard.com</a></p>
        </div>
    </div>
</body>
</html>
"""
            send_mail(
                subject=subject,
                message=message,
                from_email="noreply@talentbard.com",
                recipient_list=[email],
                fail_silently=False,
                html_message=html_message,
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to send OTP email: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response({
            "message": "OTP sent successfully to your email.",
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

            return Response({
                "message": "OTP Verified Successfully."
            }, status=status.HTTP_200_OK)

        except EmailOTP.DoesNotExist:
            return Response({"error": "No OTP found for this email."}, status=status.HTTP_400_BAD_REQUEST)