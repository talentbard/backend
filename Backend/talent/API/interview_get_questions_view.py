from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from user_profile.models import UserProfile
from talent.models import InterviewQuestion

HEADER_PARAMS = {
    'access_token': openapi.Parameter(
        'accesstoken', openapi.IN_HEADER, description="JWT access token", type=openapi.TYPE_STRING
    ),
}

class InterviewQuestionsRetrieveView(APIView):
    @swagger_auto_schema(
        operation_description="Retrieve saved interview questions for a user based on user_id.",
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
                    description="Interview question retrieval parameters",
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
                        "message": openapi.Schema(type=openapi.TYPE_STRING, description="Response message"),
                        "payload": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "interview_questions_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="Interview question set ID"),
                                    "questions": openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(type=openapi.TYPE_STRING),
                                        description="List of 10 interview questions",
                                    ),
                                    "created_at": openapi.Schema(type=openapi.TYPE_STRING, description="Creation timestamp"),
                                },
                            ),
                            description="List of saved interview question sets",
                        ),
                        "status": openapi.Schema(type=openapi.TYPE_INTEGER, description="Status code"),
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
            401: openapi.Response(
                "Unauthorized",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"error": openapi.Schema(type=openapi.TYPE_STRING, description="Error message")},
                ),
            ),
            404: openapi.Response(
                "Not Found",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={"error": openapi.Schema(type=openapi.TYPE_STRING, description="Error message")},
                ),
            ),
            500: openapi.Response(
                "Server Error",
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
        user_id = payload.get("user_id")

        # Validate user_id
        if not user_id:
            return Response(
                {"error": "user_id is required in payload", "status": 400},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = UserProfile.objects.get(id=user_id)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "User not found", "status": 404},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Fetch all saved question sets for the user
        try:
            question_sets = InterviewQuestion.objects.filter(user_id=user).order_by('-created_at')
            if not question_sets.exists():
                return Response(
                    {"error": "No interview questions found for user", "status": 404},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Prepare response payload
            payload = [
                {
                    "interview_questions_id": question.interview_questions_id,
                    "questions": question.questions,
                    "created_at": question.created_at.isoformat(),
                }
                for question in question_sets
            ]

            return Response(
                {
                    "message": "Interview questions retrieved successfully",
                    "payload": payload,
                    "status": 200,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to retrieve questions: {str(e)}", "status": 500},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )