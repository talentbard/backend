import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from talent.models import SkillsExpertise, TalentRegistrationStatus
from talent.serializers import SkillsExpertiseSerializer
from user_profile.models import UserProfile
from supabase_client import supabase  # Make sure this import works

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
                    properties={
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING),
                        "refresh_token": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                    required=["user_id", "refresh_token"],
                ),
                "payload": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
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
                            items=openapi.Items(
                                type=openapi.TYPE_STRING,
                                format="binary"
                            ),
                            description="One or more certificate image or document files."
                        ),
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING,  description="User ID"),

                    },
                    required=["user_id", "primary_skills"],
                ),
            },
            required=["payload", "auth_params"],
        ),
        consumes=["multipart/form-data"],
    )

    @authenticate_user_session
    def post(self, request):
        payload = request.data.get("payload", {})
        files = request.FILES.getlist("certificate_images")  # certificate_images[] files

        primary_skills = payload.get("primary_skills", [])
        secondary_skills = payload.get("secondary_skills", [])
        user_id = payload.get("user_id")

        if not primary_skills or not user_id:
            return Response(
                {"error": "User ID and Primary Skills are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = UserProfile.objects.get(user_id=user_id)
        except UserProfile.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Upload certificates to Supabase
        uploaded_cert_urls = []
        for file in files:
            unique_filename = f"{user_id}/{uuid.uuid4()}_{file.name}"
            res = supabase.storage.from_("certificates").upload(unique_filename, file, {"content-type": file.content_type})

            if "error" in res and res["error"]:
                return Response({"error": f"Failed to upload {file.name}: {res['error']['message']}"}, status=400)

            public_url = supabase.storage.from_("certificates").get_public_url(unique_filename)
            uploaded_cert_urls.append(public_url)

        # Save in the database
        skills_expertise = SkillsExpertiseSerializer(
            data={
                "primary_skills": primary_skills,
                "secondary_skills": secondary_skills,
                "certificate_images": uploaded_cert_urls,
                "user_id": user.user_id,
            }
        )

        if skills_expertise.is_valid():
            skills_expertise.save()
            talent_status, _ = TalentRegistrationStatus.objects.get_or_create(user_id=user_id)
            talent_status.status_id = "2"
            talent_status.save()

            return Response(
                {
                    "message": "Skills and expertise added successfully",
                    "user_data": skills_expertise.data,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(skills_expertise.errors, status=status.HTTP_400_BAD_REQUEST)
