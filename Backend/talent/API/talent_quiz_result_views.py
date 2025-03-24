from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from talent.models import QuizResult, TalentRegistrationStatus
from talent.serializers import QuizResultSerializer
from user_profile.models import UserProfile

HEADER_PARAMS = {
    'access_token': openapi.Parameter(
        'accesstoken', openapi.IN_HEADER, description="JWT access token", type=openapi.TYPE_STRING
    ),
}

class QuizResultCreateView(APIView):
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
                        "quiz_score": openapi.Schema(type=openapi.TYPE_INTEGER, description="Quiz Score"),
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                    },
                    required=["user_id", "quiz_score"],
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
                        "quiz_score": openapi.Schema(type=openapi.TYPE_INTEGER, description="Quiz Score"),
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

        quiz_score = payload.get("quiz_score")
        user_id = payload.get("user_id")

        if not quiz_score or not user_id:
            return Response(
                {"error": "User ID, Quiz Score are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = UserProfile.objects.get(user_id=user_id)

        serializer = QuizResultSerializer(
            data={
                "quiz_score": quiz_score,
                "user_id": user.user_id,
            }
        )

        if serializer.is_valid():
            quiz_result = serializer.save()
            # Update Talent Registration Status
            talent_status, _ = TalentRegistrationStatus.objects.get_or_create(user_id=user_id)
            talent_status.status_id = "9"
            talent_status.save()

            user_data = {
                "quiz_score": quiz_result.quiz_score,
            }

            return Response(
                {"message": "Quiz Result added successfully", "user_data": user_data},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 