from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from talent.models import JobPreferences
from user_profile.models import UserProfile
import google.generativeai as genai
import json, re,os

HEADER_PARAMS = {
    'access_token': openapi.Parameter(
        'accesstoken', openapi.IN_HEADER, description="JWT access token", type=openapi.TYPE_STRING
    ),
}

class TalentMakeQuizView(APIView):
    @swagger_auto_schema(
        operation_description="generate questions",
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
                    description="Quiz Generation based on skills",
                    properties={
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                    },
                    required=["user_id"],
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

                        "status": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
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
        user_id = payload.get("user_id")
        api_key = os.getenv('GEMENI_API_KEY')

        if not user_id:
            return Response({"message": "User ID is required", "status": 400}, status=status.HTTP_400_BAD_REQUEST)

        try:
            job_preference = JobPreferences.objects.get(user_id=user_id)
        except JobPreferences.DoesNotExist:
            return Response({"message": "User Job Preferences not found", "status": 404}, status=status.HTTP_404_NOT_FOUND)
        
        job_title = job_preference.job_title or "Not specified"
        industry = job_preference.industry or "Not specified"
        frameworks = job_preference.frameworks or []

        # Validate and format inputs
        job_title = str(job_title).strip()
        industry = str(industry).strip()
        frameworks = [str(f).strip() for f in frameworks] if frameworks else ["None"]

        # Prepare job context
        job_text = f"Job Title: {job_title}. Industry: {industry}. Frameworks: {', '.join(frameworks) or 'None'}"

        genai.configure(api_key=api_key)
    
        prompt = f"""
            Generate 10 professional multiple-choice questions to evaluate a freelancer's technical and domain-specific knowledge based on their job preferences. The questions should assess the freelancer's expertise level (beginner, intermediate, advanced) in the specified job title, industry, and frameworks.

            **Requirements:**
            - Generate 3 beginner-level, 4 intermediate-level, and 3 advanced-level questions to comprehensively assess knowledge depth.
            - Each question should be directly relevant to the job title, industry, and frameworks provided, reflecting real-world tasks or scenarios.
            - Questions must be solvable within 15 minutes and have a clear, unambiguous correct answer.
            - Use a professional tone, avoiding fluff or irrelevant content even try to avoid html.
            - Provide 4 answer options per question, with exactly one correct answer. Distractors should reflect common misconceptions or errors.
            - If frameworks are 'None', focus on general knowledge for the job title and industry.

            **Job Preferences:** {job_text}

            **Response Format (JSON):**
            ```json
            [
                {{
                    "question_no": 1,
                    "difficulty": "beginner",
                    "question": "Sample question here",
                    "option_1": "Option A",
                    "option_2": "Option B",
                    "option_3": "Option C",
                    "option_4": "Option D",
                    "correct_option": "Option A",                }},
                ...
            ]
            ```
        """
        
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        
        response_content = response.text if hasattr(response, 'text') else str(response)
        json_match = re.search(r'(\{.*\}|\[.*\])', response_content, re.DOTALL)
        
        if json_match:
            json_text = json_match.group(0) 
            parsed_response = json.loads(json_text)
        
        return Response({
            "message": "Questions generated successfully",
            "payload": parsed_response,
            "status": 200
        }, status=status.HTTP_200_OK)