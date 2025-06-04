from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from user_profile.models import UserProfile
from talent.models import InterviewAnswer, TalentRegistrationStatus, TalentScore
from talent.serializers import InterviewResultSerializer, TalentScoreSerializer
import requests
import json
import os, re
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
                        "cheating_suspected": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Flag indicating if cheating is suspected"),
                    },
                    required=["user_id", "answers", "cheating_suspected"],
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
                                "cheating_suspected": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Flag indicating if cheating is suspected"),
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
        cheating_suspected = payload.get("cheating_suspected", False)

        # Validate inputs
        if not user_id or not answers:
            return Response(
                {"error": "user_id and answers are required", "status": 400},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = UserProfile.objects.get(user_id=user_id)
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
            print("Raw Groq API Response:", repr(raw))  # Debug print

            if not raw.strip():
                return Response({"error": "Groq API returned empty content", "status": 500}, status=500)

            try:
                evaluation = json.loads(raw)
            except json.JSONDecodeError:
                # Attempt: Fix unclosed JSON object
                if '"score":' in raw and not raw.strip().endswith('}'):
                    raw += '}'

                # Try to fix common issues: trailing commas, missing braces
                cleaned = re.sub(r",\s*([}\]])", r"\1", raw)
                try:
                    evaluation = json.loads(cleaned)
                except json.JSONDecodeError as e2:
                    return Response(
                        {"error": f"Failed to parse Groq API response as JSON after cleaning: {str(e2)}", "status": 500},
                        status=500,
                    )


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
                score=total_score,
                cheating_suspected=cheating_suspected,
            )
        except Exception as e:
            return Response(
                {"error": f"Failed to save answers: {str(e)}", "status": 500},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Save interview score to TalentScore model
        try:
            talent_score, _ = TalentScore.objects.get_or_create(user_id=user)
            talent_score.interview_score = total_score
            talent_score.save()
        except Exception as e:
            return Response(
                {"error": f"Error updating TalentScore: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Save to InterviewResult model
        serializer = InterviewResultSerializer(
            data={
                "interview_score": str(total_score),
                "user_id": user.user_id,
            }
        )
        if serializer.is_valid():
            interview_result = serializer.save()
        else:
            return Response(
                {"error": serializer.errors, "status": 400},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update TalentRegistrationStatus based on scores
        try:
            # Fetch or create the talent status record
            talent_status, _ = TalentRegistrationStatus.objects.get_or_create(user_id=user_id)

            # Get the full score object
            score_obj = TalentScore.objects.get(user_id=user_id)

            quiz_score = score_obj.quiz_score or 0
            assignment_score = score_obj.assignment_score or 0
            interview_score_val = score_obj.interview_score or 0

            # Re-fetch latest interview answer to ensure we check against the stored value
            latest_interview_answer = InterviewAnswer.objects.filter(user_id=user).order_by('-created_at').first()

            if (
                quiz_score > 5 and
                assignment_score > 5 and
                interview_score_val > 50 and
                latest_interview_answer and
                latest_interview_answer.cheating_suspected == False
            ):
                talent_status.status_id = "11"
            else:
                talent_status.status_id = "12"



            talent_status.save()
        except TalentRegistrationStatus.DoesNotExist:
            return Response(
                {"error": "Talent registration status not found", "status": 404},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": f"Error updating registration status: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


        user_data = {
            "interview_score": interview_result.interview_score,
        }

        return Response(
            {
                "message": "Answers evaluated and saved successfully",
                "user_data": user_data,
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
    qa_text = "\n".join(
        f"Question {i+1}: {qa['question']}\nAnswer: {qa['answer']}"
        for i, qa in enumerate(question_answers)
    )
    return (
        "You are a senior technical interviewer. Evaluate the following question-answer pairs and return:\n"
        "1. A JSON object containing:\n"
        "- 'feedback': a list of objects with 'question' and 'feedback' keys.\n"
        "- 'score': a number from 0 to 100.\n"
        "Strictly return a **valid JSON object only**, with proper brackets and no extra text, explanation, or markdown.\n"
        "**Scoring rules:**\n"
        "- Answers that are irrelevant, too short (<10 words), or obviously wrong should score very low.\n"
        "- At least 70% of answers must be detailed, accurate, and relevant to receive a score over 50.\n"
        "- Use 0–10 for mostly wrong or nonsense answers.\n"
        "- Use 11–40 for partially correct answers.\n"
        "- Use 41–50 for decent but incomplete answers.\n"
        "- Use 61–100 only for very good answers with strong justification.\n"
        "- Each poor or irrelevant answer should reduce the score by 10 points.\n"
        "- Answers like 'nothing', 'no', 'ok', 'true', 'false', or 'not ok' should result in 0 points for that answer.\n"
        "- If 5 or more answers are poor or irrelevant, the total score must be less than 55.\n"
        "- If 7 or more answers are poor or irrelevant, the total score must be less than 35.\n"
        "- Only answers that are technically correct, sufficiently detailed, and relevant count as 'Good'.\n"
        "\n"
        "Example:\n"
        "{\n"
        "  \"feedback\": [\n"
        "    {\"question\": \"Question 1\", \"feedback\": \"Too short.\"},\n"
        "    {\"question\": \"Question 2\", \"feedback\": \"Good.\"}\n"
        "  ],\n"
        "  \"score\": 85\n"
        "}\n"
        "**DO NOT include markdown, quotes, or text before or after this object.**\n"
        "Do not forget to close all brackets properly. Return only this object.\n"
        f"\nEvaluate:\n{qa_text}"
    )
