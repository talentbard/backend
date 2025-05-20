from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from talent.models import JobPreferences, InterviewQuestion, PortfolioReferences
from user_profile.models import UserProfile
import json
import requests
import os, re

HEADER_PARAMS = {
    'access_token': openapi.Parameter(
        'accesstoken', openapi.IN_HEADER, description="JWT access token", type=openapi.TYPE_STRING
    ),
}

class InterviewQuestionsView(APIView):
    @swagger_auto_schema(
        operation_description="Generate and save 10 interview questions based on user's job preferences and resume text.",
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
                    description="Interview question generation parameters",
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
        try:
            # Parse auth_params and payload
            auth_params = request.data.get("auth_params", {})
            if isinstance(auth_params, str):
                try:
                    auth_params = json.loads(auth_params)
                except json.JSONDecodeError:
                    return Response(
                        {"error": "Invalid auth_params JSON format", "status": 400},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            payload = request.data.get("payload", {})
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    return Response(
                        {"error": "Invalid payload JSON format", "status": 400},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            # Extract user_id from auth_params
            user_id = auth_params.get("user_id")
            if not user_id:
                return Response(
                    {"error": "user_id is required in auth_params", "status": 400},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Validate user
            try:
                user = UserProfile.objects.get(user_id=user_id)
            except UserProfile.DoesNotExist:
                return Response(
                    {"error": "User not found", "status": 404},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Fetch job preferences
            try:
                job_prefs = JobPreferences.objects.get(user_id=user)
                domain = job_prefs.industry
                framework = job_prefs.desired_role or job_prefs.job_title
            except JobPreferences.DoesNotExist:
                return Response(
                    {"error": "Job preferences not found for user", "status": 404},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Fetch resume text
            details = ""
            try:
                portfolio = PortfolioReferences.objects.get(user_id=user)
                details = portfolio.resume or ""
            except PortfolioReferences.DoesNotExist:
                # Resume is optional, so continue without details if not found
                pass

            # Build prompt for Groq API
            prompt = build_combined_prompt(domain, framework, details)

            # Call Groq API
            try:
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"},
                    json={
                        "model": "llama3-8b-8192",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.3,
                    },
                )
                response.raise_for_status()
                response_data = response.json()
                print(response_data)
                raw = response_data["choices"][0]["message"]["content"]
                match = re.search(r"\[.*\]", raw, re.DOTALL)
                if not match:
                    raise ValueError("Could not extract a JSON array from the response.")
                questions = json.loads(match.group(0))
                if not isinstance(questions, list) or len(questions) != 10:
                    raise ValueError("Response must be a JSON array of 10 questions")
            except (requests.RequestException, ValueError, KeyError) as e:
                return Response(
                    {"error": f"Failed to generate questions: {str(e)}", "status": 500},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            # Save questions to InterviewQuestion model
            try:
                interview_question = InterviewQuestion.objects.create(
                    user_id=user,
                    questions=questions
                )
            except Exception as e:
                return Response(
                    {"error": f"Failed to save questions: {str(e)}", "status": 500},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(
                {
                    "message": "Questions generated and saved successfully",
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

# ────────────────────────────────────────────────────────────
#  Prompt builder for combined 5+5 questions
# ────────────────────────────────────────────────────────────
def build_combined_prompt(domain: str, framework: str, details: str) -> str:
    """
    Constructs a prompt that asks for:
      - Questions 1–5: Intermediate-to-advanced on the domain/framework.
      - Questions 6–10: Based on project details from the resume text.
    Each question must increase in difficulty, with at least two follow-ups building on the previous question.
    Return only a JSON array of exactly 10 question strings, no additional text.
    """
    return (
        "You are a senior technical interviewer.\n"
        "Generate a JSON array of exactly 10 interview questions following these rules:\n"
        "1. Questions 1-5: Intermediate-to-advanced questions about '" + domain + "' using '" + framework + "'.\n"
        "2. Questions 6-10: Progressive questions based on the resume details below:\n" + details + "\n"
        "Each question should increase in difficulty, and at least two questions must follow up directly on the previous question.\n"
        "Return only the JSON array of 10 strings, without any commentary."
    )