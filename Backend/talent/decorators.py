from django.http import HttpRequest
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.response import Response
from rest_framework import status
from functools import wraps
from .models import UserProfile
from rest_framework.request import Request
from uuid import UUID

# Validate access token function
def validate_access_token(access_token):
    """
    Validates the access token and retrieves the associated user.
    """
    jwt_auth = JWTAuthentication()
    validated_token = jwt_auth.get_validated_token(access_token)
    user = jwt_auth.get_user(validated_token)
    return user

# Refresh access token function
def refresh_access_token(refresh_token, user_id):
    """
    Refreshes the access token using the provided refresh token.
    """
    user = UserProfile.objects.get(user_id=user_id)  # Ensure the user exists
    refresh = RefreshToken(refresh_token)
    new_access_token = str(refresh.access_token)
    return new_access_token, user

# Decorator to authenticate user session
def authenticate_user_session(view_func):
    @wraps(view_func)
    def wrapper(view_instance, request, *args, **kwargs):
        # Ensure the request is valid
        if not isinstance(request, (HttpRequest, Request)):
            return Response(
                {"error": "Invalid request object."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Extract authentication parameters
        auth_params = request.data.get("auth_params", {})
        access_token = request.headers.get("Accesstoken", "")
        refresh_token = auth_params.get("refresh_token", "")
        user_id = auth_params.get("user_id", "")

        # Ensure an access token is provided
        if not access_token:
            return Response(
                {"error": "Access token is required."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            # Validate the access token and authenticate the user

            user_id_uuid = UUID(user_id)  # Convert user_id to UUID
            user = UserProfile.objects.get(user_id=user_id_uuid)
            request.user = user  # Attach the authenticated user to the request
            return view_func(view_instance, request, *args, **kwargs)

        except (InvalidToken, TokenError) as token_error:
            # Handle token validation failure
            if refresh_token and user_id:
                try:
                    new_access_token, user = refresh_access_token(refresh_token, user_id)
                    return Response(
                        {
                            "new_access_token": new_access_token,
                            "message": "Token refreshed successfully.",
                        },
                        status=status.HTTP_200_OK,
                    )
                except UserProfile.DoesNotExist:
                    return Response(
                        {"error": "User not found."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
                except (InvalidToken, TokenError) as refresh_error:
                    return Response(
                        {
                            "error": "Invalid or expired refresh token.",
                            "detail": str(refresh_error),
                        },
                        status=status.HTTP_401_UNAUTHORIZED,
                    )
                except Exception as unexpected_error:
                    return Response(
                        {
                            "error": "An unexpected error occurred during token refresh.",
                            "detail": str(unexpected_error),
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
            else:
                return Response(
                    {
                        "error": "Access token is invalid or expired, and no refresh token provided.",
                        "detail": str(token_error),
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        except Exception as unexpected_error:
            return Response(
                {
                    "error": "An unexpected error occurred.",
                    "detail": str(unexpected_error),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    return wrapper