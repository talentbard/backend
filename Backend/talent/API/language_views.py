from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from django.contrib.auth.hashers import make_password, check_password

HEADER_PARAMS = {
    'access_token': openapi.Parameter('accesstoken', openapi.IN_HEADER, description="local header param", type=openapi.IN_HEADER),
}
from talent.models import LanguageProficiency,TalentRegistrationStatus
from talent.serializers import LanguageProficiencySerializer

class LanguageProficiencyCreateView(APIView):
    @swagger_auto_schema(
        operation_description="Save the user's language proficiency information.",
        consumes=["application/json"],
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
                    required=["user_id","refresh_token"],
                ),
                "payload": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Language proficiency details",
                    properties={
                        "language": openapi.Schema(type=openapi.TYPE_STRING, description="Language Name"),
                        "proficiency_level": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Proficiency Level (beginner, intermediate, advanced, fluent, native)"
                        ),
                        "certification": openapi.Schema(type=openapi.TYPE_STRING, description="Certification (optional)", nullable=True),
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                    },
                    required=["language", "proficiency_level", "user_id"],
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
                        "language": openapi.Schema(type=openapi.TYPE_STRING, description="Language Name"),
                        "proficiency_level": openapi.Schema(type=openapi.TYPE_STRING, description="Proficiency Level"),
                        "certification": openapi.Schema(type=openapi.TYPE_STRING, description="Certification"),
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
        auth_params = request.data.get("auth_params", {})

        language = payload.get("language")
        proficiency_level = payload.get("proficiency_level")
        certification = payload.get("certification", None)
        user_id = payload.get("user_id")

        if not language or not proficiency_level or not user_id:
            return Response(
                {"error": "Language, proficiency level, and user ID are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = LanguageProficiencySerializer(
            data={
                "language": language,
                "proficiency_level": proficiency_level,
                "certification": certification,
                "user_id": user_id,
            }
        )

        if serializer.is_valid():
            user_language = serializer.save()
            talent_status = TalentRegistrationStatus.objects.get(user_id=user_id)
            talent_status.talent_status = "5"  # Assuming "5" is the updated status for language proficiency completion
            talent_status.save()
            user_data = {
                    "language": user_language.language,
                    "proficiency_level": user_language.proficiency_level,
                    "certification": user_language.certification,
                    "user_id": str(user_language.user_id),
                }

            return Response(
                {"message": "Language proficiency added successfully", "user_data": user_data},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
