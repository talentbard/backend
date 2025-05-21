from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from talent.models import JobPreferences
from user_profile.models import UserProfile
from talent.models import GeneratedAssignment
from talent.serializers import AssignmentResultSerializer
import google.generativeai as genai
import json
import re
import os

HEADER_PARAMS = {
    'access_token': openapi.Parameter(
        'accesstoken', openapi.IN_HEADER, description="JWT access token", type=openapi.TYPE_STRING
    ),
}

class TalentMakeAssignmentView(APIView):
    @swagger_auto_schema(
        operation_description="Generate or retrieve a practical assignment based on user's job preferences to evaluate thought process and creativity.",
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
                    description="Assignment generation based on job preferences",
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
                        "status": openapi.Schema(type=openapi.TYPE_STRING, description="Status message"),
                        "payload": openapi.Schema(type=openapi.TYPE_OBJECT, description="Generated or retrieved assignment"),
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
                "Not Found",
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
        api_key = os.getenv('GEMENI_API_KEY')

        if not user_id:
            return Response({"message": "User ID is required", "status": 400}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = UserProfile.objects.get(user_id=user_id)
        except UserProfile.DoesNotExist:
            return Response({"message": "User profile not found", "status": 404}, status=status.HTTP_404_NOT_FOUND)

        # Check if assignment already exists
        try:
            existing_assignment = GeneratedAssignment.objects.get(user=user)
            return Response({
                "message": "Assignment retrieved successfully",
                "payload": existing_assignment.assignment_task,
                "status": 200
            }, status=status.HTTP_200_OK)
        except GeneratedAssignment.DoesNotExist:
            pass

        try:
            job_preference = JobPreferences.objects.get(user_id=user_id)
        except JobPreferences.DoesNotExist:
            return Response({"message": "User Job Preferences not found", "status": 404}, status=status.HTTP_404_NOT_FOUND)
        
        job_title = job_preference.job_title or "Not specified"
        industry = job_preference.industry or "Not specified"
        frameworks = job_preference.frameworks or []

        job_title = str(job_title).strip()
        industry = str(industry).strip()
        frameworks = [str(f).strip() for f in frameworks] if frameworks else ["None"]

        job_context = f"Job Title: {job_title}. Industry: {industry}. Frameworks: {', '.join(frameworks)}"

        genai.configure(api_key=api_key)

        prompt = f"""
            Generate a professional and practical assignment based on the freelancer's job preferences to evaluate their thought process, creativity, and problem-solving skills in real-world scenarios.

            **Requirements:**
            - The assignment must reflect a **real-world problem** relevant to the job title, industry, and frameworks, encouraging creative and practical solutions.
            - The task should be **solvable within 1-2 days** and match the inferred skill level (Beginner, Intermediate, or Advanced) based on the job context.
            - Include a requirement for the freelancer to **document their thought process** (e.g., rationale, design decisions, or trade-offs) as part of the deliverables.
            - Ensure the task is **open-ended enough** to allow creativity but includes **clear constraints** to maintain focus.
            - Define **expected deliverables** (e.g., code, documentation, design mockups) and **evaluation criteria** (e.g., functionality, creativity, scalability, clarity of thought process).
            - If frameworks are 'None', focus on core skills relevant to the job title and industry.
            - Use a **professional tone** and avoid unnecessary complexity or fluff.

            **Job Preferences:** {job_context}

            **Response Format (JSON):**
            ```json
            {{
                "task_title": "Short title summarizing the task",
                "task_description": "Detailed description of the real-world problem, including context, requirements, and constraints",
                "expected_deliverables": [
                    "Deliverable 1 (e.g., working code implementing the solution)",
                    "Deliverable 2 (e.g., documentation of thought process and design decisions)",
                    "Deliverable 3 (e.g., any additional assets like mockups or tests)"
                ],
                "difficulty_level": "Beginner / Intermediate / Advanced",
                "evaluation_criteria": [
                    "Criteria 1 (e.g., Correctness and functionality of the solution)",
                    "Criteria 2 (e.g., Creativity and innovation in the approach)",
                    "Criteria 3 (e.g., Clarity and quality of documented thought process)"
                ]
            }}
            ```
        """

        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            response_content = response.text if hasattr(response, 'text') else str(response)

            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if not json_match:
                return Response({"message": "Failed to parse JSON response", "status": 500}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            json_text = json_match.group(0)
            parsed_response = json.loads(json_text)

            required_keys = ["task_title", "task_description", "expected_deliverables", "difficulty_level", "evaluation_criteria"]
            if not isinstance(parsed_response, dict) or not all(key in parsed_response for key in required_keys):
                return Response({"message": "Invalid response format from AI model", "status": 500}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Save assignment to GeneratedAssignment
            GeneratedAssignment.objects.create(
                user=user,
                assignment_task=parsed_response
            )

            return Response({
                "message": "Assignment generated successfully",
                "payload": parsed_response,
                "status": 200
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "message": f"Error generating assignment: {str(e)}",
                "status": 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)