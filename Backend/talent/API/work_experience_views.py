from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from talent.models import WorkExperience, TalentRegistrationStatus
from talent.serializers import WorkExperienceSerializer
from user_profile.models import UserProfile

HEADER_PARAMS = {
    'access_token': openapi.Parameter(
        'accesstoken', openapi.IN_HEADER, description="JWT access token", type=openapi.TYPE_STRING
    ),
}

class WorkExperienceCreateView(APIView):
    @swagger_auto_schema(
        operation_description="Add work experience for a user.",
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
                    description="Work experience details",
                    properties={
                        "job_title": openapi.Schema(type=openapi.TYPE_STRING, descrer_idiption="Job title"),
                        "company": openapi.Schema(type=openapi.TYPE_STRING, description="Company name"),
                        "industry": openapi.Schema(type=openapi.TYPE_STRING, description="Industry"),
                        "start_date": openapi.Schema(type=openapi.TYPE_STRING, format="date", description="Start date (YYYY-MM-DD)"),
                        "end_date": openapi.Schema(type=openapi.TYPE_STRING, format="date", description="End date (YYYY-MM-DD, optional)"),
                        "responsibilities": openapi.Schema(type=openapi.TYPE_STRING, description="Responsibilities"),
                        "achievements": openapi.Schema(type=openapi.TYPE_STRING, description="Achievements"),
                        "technologies_used": openapi.Schema(type=openapi.TYPE_STRING, description="Technologies used"),
                        "projects": openapi.Schema(type=openapi.TYPE_STRING, description="Projects handled"),
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                    },
                    required=["user_id", "job_title", "company", "industry", "start_date", "responsibilities", "achievements","technologies_used", "projects"],
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
                        "job_title": openapi.Schema(type=openapi.TYPE_STRING, description="Job title"),
                        "company": openapi.Schema(type=openapi.TYPE_STRING, description="Company name"),
                        "industry": openapi.Schema(type=openapi.TYPE_STRING, description="Industry"),
                        "start_date": openapi.Schema(type=openapi.TYPE_STRING, format="date", description="Start date"),
                        "end_date": openapi.Schema(type=openapi.TYPE_STRING, format="date", description="End date"),
                        "responsibilities": openapi.Schema(type=openapi.TYPE_STRING, description="Responsibilities"),
                        "achievements": openapi.Schema(type=openapi.TYPE_STRING, description="Achievements"),
                        "technologies_used": openapi.Schema(type=openapi.TYPE_STRING, description="Technologies used"),
                        "projects": openapi.Schema(type=openapi.TYPE_STRING, description="Projects"),
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                    },
                ),
            ),
            400: openapi.Response(
                "Bad Request",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"error": openapi.Schema(type=openapi.TYPE_STRING, description="Error message")},
                ),
            ),
            404: openapi.Response(
                "User Not Found",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"error": openapi.Schema(type=openapi.TYPE_STRING, description="Error message")},
                ),
            ),
            401: openapi.Response(
                "Unauthorized",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"error": openapi.Schema(type=openapi.TYPE_STRING, description="Error message")},
                ),
            ),
        },
    )
    @authenticate_user_session
    def post(self, request):
        payload = request.data.get("payload", {})

        job_title = payload.get("job_title")
        company = payload.get("company")
        industry = payload.get("industry")
        start_date = payload.get("start_date")
        end_date = payload.get("end_date")
        responsibilities = payload.get("responsibilities")
        achievements = payload.get("achievements")
        technologies_used = payload.get("technologies_used")
        projects = payload.get("projects")
        user_id = payload.get("user_id")

        if not job_title or not company or not industry or not start_date or not user_id or not responsibilities or not achievements or not technologies_used or not projects:
            return Response(
                {"error": "User ID, Job Title, Company, Industry, Start Date, Responsibilities, Achievements, Technologies used, Projects are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = UserProfile.objects.get(user_id=user_id)

        serializer = WorkExperienceSerializer(
            data={
                "job_title": job_title,
                "company": company,
                "industry": industry,
                "start_date": start_date,
                "end_date": end_date,
                "responsibilities": responsibilities,
                "achievements": achievements,
                "technologies_used": technologies_used,
                "projects": projects,
                "user_id": user.user_id,
            }
        )

        if serializer.is_valid():
            work_experience = serializer.save()
            # Update Talent Registration Status
            talent_status, _ = TalentRegistrationStatus.objects.get_or_create(user_id=user_id)
            talent_status.status_id = "4"
            talent_status.save()

            user_data = {
                "job_title": work_experience.job_title,
                "company": work_experience.company,
                "industry": work_experience.industry,
                "start_date": work_experience.start_date,
                "end_date": work_experience.end_date,
                "responsibilities": work_experience.responsibilities,
                "achievements": work_experience.achievements,
                "technologies_used": work_experience.technologies_used,
                "projects": work_experience.projects,
            }

            return Response(
                {"message": "Work experience added successfully", "user_data": user_data},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 