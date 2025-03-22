from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from talent.models import SkillsExpertise, TalentRegistrationStatus
from talent.serializers import SkillsExpertiseSerializer
from user_profile.models import UserProfile

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
                        "primary_skills": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "skill_name": openapi.Schema(type=openapi.TYPE_STRING, description="Primary skill name"),
                                    "skill_level": openapi.Schema(type=openapi.TYPE_STRING, description="Skill level"),
                                    "experience_years": openapi.Schema(type=openapi.TYPE_INTEGER, description="Years of experience"),
                                },
                            ),
                            description="List of primary skills with name, level, and experience",
                        ),
                        "secondary_skills": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "skill_name": openapi.Schema(type=openapi.TYPE_STRING, description="Secondary skill name"),
                                    "skill_level": openapi.Schema(type=openapi.TYPE_STRING, description="Skill level"),
                                    "experience_years": openapi.Schema(type=openapi.TYPE_INTEGER, description="Years of experience"),
                                },
                            ),
                            description="List of secondary skills with name, level, and experience",
                        ),
                        "certificate_images": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(type=openapi.TYPE_STRING, format="binary"),
                            description="List of uploaded certificate files",
                        ),
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                    },
                    required=["user_id", "primary_skills"],
                ),
            },
            required=["payload", "auth_params"],
        ),
        responses={
            201: openapi.Response(
                "Success",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "primary_skills": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(type=openapi.TYPE_OBJECT),
                        ),
                        "secondary_skills": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(type=openapi.TYPE_OBJECT),
                        ),
                        "certificate_images": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Items(type=openapi.TYPE_STRING),
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
        payload = request.data.get("payload", {})
        
        primary_skills = payload.get("primary_skills", [])
        secondary_skills = payload.get("secondary_skills", [])
        certificate_images = payload.get("certificates", [])
        user_id = payload.get("user_id")

        if not primary_skills or not user_id :
            return Response(
                {"error": "User ID and Primary Skills are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        user = UserProfile.objects.get(user_id=user_id)
        
        skills_expertise = SkillsExpertiseSerializer(
            data={
                "primary_skills":primary_skills,
                "secondary_skills":secondary_skills,
                "certificate_images":certificate_images,
                "user_id": user.user_id,
            }
        )
        if skills_expertise.is_valid():
            talent_status, _ = TalentRegistrationStatus.objects.get_or_create(user_id=user_id)
            talent_status.status_id = "2"
            talent_status.save()

            user_data = {
                "primary_skills": skills_expertise.validated_data.get("primary_skills"),
                "secondary_skills": skills_expertise.validated_data.get("secondary_skills"),
                "certificate_images": skills_expertise.validated_data.get("certificate_images"),
            }

            return Response(
                {"message": "Skills and expertise added successfully", "user_data": user_data},
                status=status.HTTP_201_CREATED,
            )

        return Response(skills_expertise.errors, status=status.HTTP_400_BAD_REQUEST)