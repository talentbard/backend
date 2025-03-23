from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from talent.models import SkillsExpertise
from user_profile.models import UserProfile
from google import genai
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
                    description="Talent registration details",
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
        # import pdb;pdb.set_trace()

        user_id = payload.get("user_id")
        api_key = os.getenv('GEMENI_API_KEY')

        try:
            skills_expertise = SkillsExpertise.objects.get(user_id=user_id)
        except SkillsExpertise.DoesNotExist:
            return Response({"message": "User skills not found", "status": 404}, status=status.HTTP_404_NOT_FOUND)
        
        primary_skills = skills_expertise.primary_skills
        secondary_skills = skills_expertise.secondary_skills or []
        
        # Prepare API prompt
        skill_text = f"Primary skills: {', '.join(primary_skills)}. Secondary skills: {', '.join(secondary_skills)}."

        client = genai.Client(api_key=api_key)

        prompt=f'''I want 10 questions based on the skills I am mentioning below and those questions should be solveable within 10 mins
                  ,these questions are for hiring freelancers.I want the questions in multiple choice of 4 options along with the correct option
                  skills: {skill_text}
                  i want the reponse to be in json format:
                  question_no:1
                  option_1:
                  option_2:
                  option_3:
                  option_4:
                  correct_option:, ......
                  '''

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        
        response_content = response.text if hasattr(response, 'text') else str(response)
        
        json_match = re.search(r'(\{.*\}|\[.*\])', response_content, re.DOTALL)
        
        if json_match:
            json_text = json_match.group(0) 
            parsed_response = json.loads(json_text)
            # formatted_response = format_response_for_readability(parsed_response)
            # return formatted_response
        print(parsed_response)
        if response.status_code == 200:
            return Response({
                "message": "Questions generated successfully",
                "payload": parsed_response,
                "status": 200
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "message": "Failed to generate questions",
                "payload": response.json(),
                "status": response.status_code
            }, status=response.status_code)
