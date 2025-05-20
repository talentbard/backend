from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from user_profile.models import UserProfile
from talent.models import InterviewAnswer ,TalentRegistrationStatus
import requests
import json
import os
from django.conf import settings

HEADER_PARAMS = {
    'access_token': openapi.Parameter(
        'accesstoken', openapi.IN_HEADER, description="JWT access token", type=openapi.TYPE_STRING
    ),
}

class InterviewAnswersSaveView(APIView):
    @swagger_auto_schema(
        operation_description="Save candidate answers with questions, evaluate them using Groq AI, and store the score.",
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
                    description="Interview answer submission parameters",
                    properties={
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                        "answers": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "question": openapi.Schema(type=openapi.TYPE_STRING, description="Interview question"),
                                    "answer": openapi.Schema(type=openapi.TYPE_STRING, description="Candidate's answer"),
                                },
                            ),
                            description="List of question-answer pairs",
                        ),
                    },
                    required=["user_id", "answers"],
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
                                "interview_answer_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="Interview answer set ID"),
                                "question_answers": openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            "question": openapi.Schema(type=openapi.TYPE_STRING, description="Question"),
                                            "answer": openapi.Schema(type=openapi.TYPE_STRING, description="Candidate's answer"),
                                            "feedback": openapi.Schema(type=openapi.TYPE_STRING, description="Evaluation feedback"),
                                        },
                                    ),
                                    description="List of question-answer pairs with feedback",
                                ),
                                "score": openapi.Schema(type=openapi.TYPE_NUMBER, description="Evaluation score out of 100"),
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
        payload = request.data.get("payload", {})
        user_id = payload.get("user_id")
        answers = payload.get("answers", [])

        # Validate inputs
        if not user_id or not answers:
            return Response(
                {"error": "user_id and answers are required", "status": 400},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = UserProfile.objects.get(id=user_id)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "User not found", "status": 404},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Validate answers format
        if not all(isinstance(a, dict) and "question" in a and "answer" in a for a in answers):
            return Response(
                {"error": "Each answer must contain 'question' and 'answer' fields", "status": 400},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Prepare question-answer pairs for evaluation
        question_answers = [
            {"question": a["question"], "answer": a["answer"], "feedback": ""}
            for a in answers
        ]

        # Build prompt for Groq API to evaluate answers
        evaluation_prompt = build_evaluation_prompt(question_answers)

        # Call Groq API to evaluate answers
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}"},
                json={
                    "model": "llama3-8b-8192",
                    "messages": [{"role": "user", "content": evaluation_prompt}],
                    "temperature": 0.3,
                },
            )
            response.raise_for_status()
            response_data = response.json()
            raw = response_data["choices"][0]["message"]["content"]
            evaluation = json.loads(raw)
            if not isinstance(evaluation, dict) or "feedback" not in evaluation or "score" not in evaluation:
                raise ValueError("Evaluation response must contain feedback and score")
            
            # Update question_answers with feedback and compute score
            total_score = evaluation.get("score")
            for qa, fb in zip(question_answers, evaluation["feedback"]):
                qa["feedback"] = fb.get("feedback", "No feedback provided")
        except (requests.RequestException, ValueError, KeyError) as e:
            return Response(
                {"error": f"Failed to evaluate answers: {str(e)}", "status": 500},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Save to InterviewAnswer model
        try:
            interview_answer = InterviewAnswer.objects.create(
                user_id=user,
                question_answers=question_answers,
                score=total_score
            )
            talent_status = TalentRegistrationStatus.objects.get(user_id=user_id)
            # Update talent_status
            talent_status.talent_status = "11"
            # Save the changes
            talent_status.save()
        except Exception as e:
            return Response(
                {"error": f"Failed to save answers: {str(e)}", "status": 500},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "message": "Answers evaluated and saved successfully",
                "payload": {
                    "interview_answer_id": interview_answer.interview_answer_id,
                    "question_answers": interview_answer.question_answers,
                    "score": interview_answer.score,
                    "created_at": interview_answer.created_at.isoformat(),
                },
                "status": 200,
            },
            status=status.HTTP_200_OK,
        )

def build_evaluation_prompt(question_answers):
    """
    Constructs a prompt to evaluate answers and return feedback and a score.
    """
    qa_text = "\n".join(
        f"Question {i+1}: {qa['question']}\nAnswer: {qa['answer']}"
        for i, qa in enumerate(question_answers)
    )
    return (
        "You are a senior technical interviewer. Evaluate the following question-answer pairs and provide:\n"
        "1. Feedback for each answer, highlighting strengths and areas for improvement.\n"
        "2. An overall score out of 100 based on accuracy, completeness, and relevance.\n"
        "Return a JSON object with:\n"
        "- 'feedback': Array of objects with 'question' and 'feedback' fields.\n"
        "- 'score': Overall score (0-100).\n"
        f"Question-Answer Pairs:\n{qa_text}\n"
        "Return only the JSON object, no additional text."
    )