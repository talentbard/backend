from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import models
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from user_profile.models import UserProfile
from company.models import CompanyRegistration
from company.serializers import CompanyRegistrationSerializer

HEADER_PARAMS = {
    'access_token': openapi.Parameter('accesstoken', openapi.IN_HEADER, description="local header param", type=openapi.TYPE_STRING),
}

class ProfileCreateView(APIView):
    @swagger_auto_schema(
        operation_description="Retrieve the registered company profile for the given user ID.",
        manual_parameters=[HEADER_PARAMS['access_token']],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "auth_params": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Authentication parameters",
                    properties={
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                        "refresh_token": openapi.Schema(type=openapi.TYPE_STRING, description="Refresh token"),
                    },
                    required=["user_id", "refresh_token"],
                ),
                "payload": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="User payload containing user ID",
                    properties={
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                    },
                    required=["user_id"],
                ),
            },
            required=["payload", "auth_params"],
        ),
        responses={
            200: openapi.Response(
                "Success",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "profile": openapi.Schema(type=openapi.TYPE_OBJECT),
                        "status": openapi.Schema(type=openapi.TYPE_INTEGER)
                    },
                ),
            ),
            400: openapi.Response(
                "Bad Request",
                openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    "error": openapi.Schema(type=openapi.TYPE_STRING)
                }),
            ),
            404: openapi.Response(
                "Not Found",
                openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    "error": openapi.Schema(type=openapi.TYPE_STRING)
                }),
            ),
            401: openapi.Response(
                "Unauthorized",
                openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    "error": openapi.Schema(type=openapi.TYPE_STRING)
                }),
            ),
        },
    )
    @authenticate_user_session
    def post(self, request):
        payload = request.data.get("payload", {})
        user_id = payload.get("user_id")

        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = UserProfile.objects.get(user_id=user_id)
        except UserProfile.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Fetch sections of the company profile
        company_profile_qs = CompanyRegistration.objects.filter(user_id=user_id)

        # Serialize sections
        company_profile_data = CompanyRegistrationSerializer(company_profile_qs, many=True).data
        # Construct full profile
        profile = {
            "company": company_profile_data,
        }

        return Response(
            {
                "message": "Company profile retrieved successfully",
                "profile": profile,
                "status": 200
            },
            status=status.HTTP_200_OK
        )
