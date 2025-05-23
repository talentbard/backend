from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from django.contrib.auth.hashers import make_password, check_password
from talent.models import JobPreferences
from talent.serializers import JobPreferencesSerializer
from user_profile.models import UserProfile
from talent.models import Education, TalentRegistrationStatus
from talent.serializers import EducationSerializer

HEADER_PARAMS = {
    'access_token': openapi.Parameter('accesstoken', openapi.IN_HEADER, description="local header param", type=openapi.TYPE_STRING),
}

class JobPreferencesCreateView(APIView):
    @swagger_auto_schema(
        operation_description="Save the user's job preferences using `auth_params`.",
        consumes=["application/json"],
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
                    required=["user_id", "refresh_token"],
                ),
                "payload": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="User job preferences details",
                    properties={
                        "job_title": openapi.Schema(type=openapi.TYPE_STRING, description="Job Title"),
                        "industry": openapi.Schema(type=openapi.TYPE_STRING, description="Industry"),
                        "frameworks": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            description="List of frameworks",
                            items=openapi.Schema(type=openapi.TYPE_STRING)
                        ),
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                    },
                    required=["job_title", "industry", "user_id"],
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
                        "job_title": openapi.Schema(type=openapi.TYPE_STRING, description="Job Title"),
                        "industry": openapi.Schema(type=openapi.TYPE_STRING, description="Industry"),
                        "frameworks": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            description="List of frameworks",
                            items=openapi.Schema(type=openapi.TYPE_STRING)
                        ),
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
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
        payload = request.data.get('payload', {})
        job_title = payload.get('job_title')
        industry = payload.get('industry')
        frameworks = payload.get('frameworks', [])
        user_id = payload.get('user_id')

        if not job_title or not industry:
            return Response(
                {"error": "Job title and industry are required in the payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = UserProfile.objects.get(user_id=user_id)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = JobPreferencesSerializer(
            data={
                "job_title": job_title,
                "industry": industry,
                "frameworks": frameworks,
                "user_id": user.user_id,
            }
        )
        if serializer.is_valid():
            job_preference = serializer.save()
            # Retrieve the object by user_id
            talent_status = TalentRegistrationStatus.objects.get(user_id=user_id)
            # Update talent_status
            talent_status.status_id = "8"
            # Save the changes
            talent_status.save()
            user_data = {
                "job_title": job_preference.job_title,
                "industry": job_preference.industry,
                "frameworks": job_preference.frameworks,
                "user_id": user.user_id,
            }

            return Response(
                {"message": "Job Preferences saved successfully", "user_data": user_data},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)