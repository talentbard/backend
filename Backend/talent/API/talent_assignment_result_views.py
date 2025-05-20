from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from talent.models import AssignmentResult, TalentRegistrationStatus
from user_profile.models import UserProfile
from talent.serializers import TalentScoreSerializer
import google.generativeai as genai
import json, re, os

HEADER_PARAMS = {
    'access_token': openapi.Parameter(
        'accesstoken', openapi.IN_HEADER, description="JWT access token", type=openapi.TYPE_STRING
    ),
}

class AssignmentResultCreateView(APIView):
    @swagger_auto_schema(
        operation_description="Stores assignment score of user",
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
                    description="Assignment details",
                    properties={
                        "assignment_task": openapi.Schema(type=openapi.TYPE_STRING, description="Assignment Task"),
                        "assignment_submission": openapi.Schema(type=openapi.TYPE_STRING, description="Assignment Submission"),
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                    },
                    required=["user_id", "assignment_task", "assignment_submission"],
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

        assignment_submission = payload.get("assignment_submission")
        assignment_task = payload.get("assignment_task")
        user_id = payload.get("user_id")

        if not assignment_submission or not user_id or not assignment_task:
            return Response(
                {"error": "User ID, Assignment Score, Assignment Task are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = UserProfile.objects.get(user_id=user_id)

        api_key = os.getenv('GEMENI_API_KEY')
        genai.configure(api_key=api_key)

        prompt = f'''
            Evaluate the provided task submission from the given GitHub link based on the specified skills. The evaluation should be **objective, structured, and provide a score from 1 to 10**, reflecting the quality and completeness of the submission.  

            **Evaluation Criteria:**  
            - **Relevance to the Given Skills**: Does the solution effectively demonstrate expertise in the specified skills?  
            - **Code Quality & Best Practices**: Is the code well-structured, readable, and maintainable? Are best practices followed?  
            - **Functionality & Correctness**: Does the submission fully meet the requirements and function correctly?  
            - **Efficiency & Optimization**: Is the solution optimized for performance and scalability (if applicable)?  
            - **Documentation & Readability**: Are there sufficient comments, a README, and necessary explanations?  
            - **Completeness**: Does the submission meet all expected deliverables?  
            Please do give me the accurate rating in the scale of 1 to 10.

            **Assignment Task:** {assignment_task}  
            **GitHub Link:** {assignment_submission}  

            **Response Format (JSON):**  
            ```json
            {{
              "score": "String (1 to 10)"
            }}
            ```  
            Where the score is a number between 1 and 10. Do not return any extra text, comments, or formatting. The response should be a JSON object with the score only.
        '''

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)

        response_content = response.text if hasattr(response, 'text') else str(response)
        json_match = re.search(r'(\{.*\}|\[.*\])', response_content, re.DOTALL)

        if json_match:
            json_text = json_match.group(0)
            parsed_response = json.loads(json_text)
        else:
            return Response({"error": "Could not extract score from response"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        score = parsed_response["score"]
        print("Evaluated Score:", score)

        # Save score in the AssignmentResult model
        assignment_model, _ = AssignmentResult.objects.get_or_create(user_id=user_id)
        assignment_model.assignment_score = score
        assignment_model.assignment_submission = assignment_submission
        assignment_model.save()

        # Serialize using the score from Gemini, not from payload
        serializer = TalentScoreSerializer(
            data={
                "assignment_score": score,
                "user_id": user.user_id,
            }
        )

        if serializer.is_valid():
            assignment_result = serializer.save()

            # Update Talent Registration Status
            talent_status, _ = TalentRegistrationStatus.objects.get_or_create(user_id=user_id)
            talent_status.status_id = "10"
            talent_status.save()
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_data = {
            "assignment_score": assignment_result.assignment_score,
        }

        return Response(
            {"message": "Quiz Result added successfully", "user_data": user_data},
            status=status.HTTP_201_CREATED,
        )
