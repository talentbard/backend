from rest_framework.views import APIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from talent.models import InterviewQuestion
from user_profile.models import UserProfile

HEADER_PARAMS = {
    'access_token': openapi.Parameter(
        'accesstoken', openapi.IN_HEADER, description="JWT access token", type=openapi.TYPE_STRING
    ),
}

class InterviewQuestionsRetrieveView(APIView):
    @swagger_auto_schema(
        operation_description="Retrieve interview questions for a user.",
        manual_parameters=[HEADER_PARAMS['access_token']],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "auth_params": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                        "refresh_token": openapi.Schema(type=openapi.TYPE_STRING, description="Refresh token"),
                    },
                    required=["user_id", "refresh_token"],
                ),
                "payload": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                    },
                    required=["user_id"],
                ),
            },
            required=["auth_params", "payload"],
        ),
        responses={
            200: openapi.Response(
                "Success",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "payload": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "interview_questions_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "questions": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(type=openapi.TYPE_STRING),
                                    description="List of 10 interview questions",
                                ),
                                "created_at": openapi.Schema(type=openapi.TYPE_STRING),
                            },
                        ),
                        "status": openapi.Schema(type=openapi.TYPE_INTEGER),
                    },
                ),
            ),
            404: "Not Found",
            500: "Server Error",
        },
    )
    @authenticate_user_session
    def post(self, request):
        try:
            auth_params = request.data.get("auth_params", {})
            user_id = auth_params.get("user_id")

            if not user_id:
                return Response(
                    {"error": "user_id is required in auth_params", "status": 400},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            try:
                user = UserProfile.objects.get(user_id=user_id)
            except UserProfile.DoesNotExist:
                return Response(
                    {"error": "User not found", "status": 404},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Retrieve the latest InterviewQuestion entry for the user
            try:
                interview_question = InterviewQuestion.objects.filter(user_id=user).order_by('-created_at').first()
                if not interview_question:
                    return Response(
                        {"error": "No interview questions found for user", "status": 404},
                        status=status.HTTP_404_NOT_FOUND,
                    )
            except Exception as e:
                return Response(
                    {"error": f"Failed to retrieve questions: {str(e)}", "status": 500},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Validate the number of questions
            if not isinstance(interview_question.questions, list) or len(interview_question.questions) != 10:
                return Response(
                    {"error": f"Invalid number of questions retrieved: expected 10, got {len(interview_question.questions) if isinstance(interview_question.questions, list) else 'not a list'}", "status": 500},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(
                {
                    "message": "Questions retrieved successfully",
                    "payload": {
                        "interview_questions_id": interview_question.interview_questions_id,
                        "questions": interview_question.questions,
                        "created_at": interview_question.created_at.isoformat(),
                    },
                    "status": 200,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}", "status": 500},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )