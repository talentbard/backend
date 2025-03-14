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
HEADER_PARAMS = {
    'access_token': openapi.Parameter('accesstoken', openapi.IN_HEADER, description="local header param", type=openapi.IN_HEADER),
}
from talent.models import Education,TalentRegistrationStatus
from talent.serializers import EducationSerializer

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
                        "preferred_job_type": openapi.Schema(type=openapi.TYPE_STRING, description="Preferred Job Type"),
                        "industry": openapi.Schema(type=openapi.TYPE_STRING, description="Industry"),
                        "desired_role": openapi.Schema(type=openapi.TYPE_STRING, description="Desired Role"),
                        "career_objective": openapi.Schema(type=openapi.TYPE_STRING, description="Career Objective"),
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                    },
                    required=["job_title", "preferred_job_type", "industry", "user_id"],
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
                        "preferred_job_type": openapi.Schema(type=openapi.TYPE_STRING, description="Preferred Job Type"),
                        "industry": openapi.Schema(type=openapi.TYPE_STRING, description="Industry"),
                        "desired_role": openapi.Schema(type=openapi.TYPE_STRING, description="Desired Role"),
                        "career_objective": openapi.Schema(type=openapi.TYPE_STRING, description="Career Objective"),
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
        preferred_job_type = payload.get('preferred_job_type')
        industry = payload.get('industry')
        desired_role = payload.get('desired_role')
        career_objective = payload.get('career_objective')
        user_id = payload.get('user_id')

        if not job_title or not preferred_job_type or not industry:
            return Response(
                {"error": "Job title, preferred job type, and industry are required in the payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = UserProfile.objects.get(user_id=user_id)

        serializer = JobPreferencesSerializer(
            data={
                "job_title": job_title,
                "preferred_job_type": preferred_job_type,
                "industry": industry,
                "desired_role": desired_role,
                "career_objective": career_objective,
                "user_id": user.user_id,
            }
        )
        if serializer.is_valid():
            job_preference = serializer.save()
            user = serializer.save()
            # Retrieve the object by user_id
            talent_status = TalentRegistrationStatus.objects.get(user_id=user_id)
            # Update talent_status
            talent_status.talent_status = "8"
            # Save the changes
            talent_status.save()
            user_data = {
                "user_id": str(job_preference.user_id),
                "job_title": job_preference.job_title,
                "preferred_job_type": job_preference.preferred_job_type,
                "industry": job_preference.industry,
                "desired_role": job_preference.desired_role,
                "career_objective": job_preference.career_objective,
            }

            return Response(
                {"message": "Job Preferences saved successfully", "user_data": user_data},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)