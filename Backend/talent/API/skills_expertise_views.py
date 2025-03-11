from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from talent.models import SkillsExpertise, TalentRegistrationStatus
from talent.serializers import SkillsExpertiseSerializer

HEADER_PARAMS = {
    'access_token': openapi.Parameter(
        'accesstoken', openapi.IN_HEADER, description="JWT access token", type=openapi.TYPE_STRING
    ),
}

class SkillsExpertiseCreateView(APIView):
    @swagger_auto_schema(
        operation_description="Save user's skills and expertise.",
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
                    description="Skills and expertise details",
                    properties={
                        "primary_skill": openapi.Schema(type=openapi.TYPE_STRING, description="Primary skill"),
                        "skill_level": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Skill level (beginner, intermediate, expert)",
                        ),
                        "experience_years": openapi.Schema(type=openapi.TYPE_INTEGER, description="Years of experience"),
                        "secondary_skills": openapi.Schema(type=openapi.TYPE_STRING, description="Secondary skills"),
                        "certificate_image": openapi.Schema(type=openapi.TYPE_STRING, format="binary", description="Certificate image"),
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                    },
                    required=["user_id", "primary_skill", "skill_level"],
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
                        "primary_skill": openapi.Schema(type=openapi.TYPE_STRING, description="Primary skill"),
                        "skill_level": openapi.Schema(type=openapi.TYPE_STRING, description="Skill level"),
                        "experience_years": openapi.Schema(type=openapi.TYPE_INTEGER, description="Years of experience"),
                        "secondary_skills": openapi.Schema(type=openapi.TYPE_STRING, description="Secondary skills"),
                        "certificate_image": openapi.Schema(type=openapi.TYPE_STRING, description="Certificate image URL"),
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

        primary_skill = payload.get("primary_skill")
        skill_level = payload.get("skill_level")
        experience_years = payload.get("experience_years")
        secondary_skills = payload.get("secondary_skills")
        certificate_image = request.FILES.get("certificate_image")  # Handling file upload
        user_id = payload.get("user_id")

        if not primary_skill or not skill_level or not user_id:
            return Response(
                {"error": "User ID, Primary Skill, and Skill Level are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = SkillsExpertiseSerializer(
            data={
                "primary_skill": primary_skill,
                "skill_level": skill_level,
                "experience_years": experience_years,
                "secondary_skills": secondary_skills,
                "certificate_image": certificate_image,
                "user_id": user_id,
            }
        )

        if serializer.is_valid():
            skills_expertise = serializer.save()
            # Update Talent Registration Status
            talent_status, _ = TalentRegistrationStatus.objects.get_or_create(user_id=user_id)
            talent_status.status_id = "2" 
            talent_status.save()

            user_data = {
                "primary_skill": skills_expertise.primary_skill,
                "skill_level": skills_expertise.skill_level,
                "experience_years": skills_expertise.experience_years,
                "secondary_skills": skills_expertise.secondary_skills,
                "certificate_image": skills_expertise.certificate_image.url if skills_expertise.certificate_image else None,
                "user_id": str(skills_expertise.user_id),
            }

            return Response(
                {"message": "Skills and expertise added successfully", "user_data": user_data},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
