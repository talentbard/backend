from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from talent.models import SkillsExpertise
from user_profile.models import UserProfile
import google.generativeai as genai
import json, re, os
from talent.serializers import AssignmentResultSerializer


HEADER_PARAMS = {
    'access_token': openapi.Parameter(
        'accesstoken', openapi.IN_HEADER, description="JWT access token", type=openapi.TYPE_STRING
    ),
}

class TalentMakeAssignmentView(APIView):
    @swagger_auto_schema(
        operation_description="generate task",
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
                    description="Assinment Genration based on skill set",
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
        primary_skills = str(primary_skills)
        secondary_skills = str(secondary_skills)

        # Prepare API prompt
        skill_text = f"Primary skills: {', '.join(primary_skills)}. Secondary skills: {', '.join(secondary_skills)}."

        genai.configure(api_key = api_key)
    
        prompt = f'''
            Generate a professional and practical task based on the following skills. The task should be designed to effectively assess a freelancer's technical expertise.  

            **Requirements:**  
            - The task should be **realistic, practical, and solvable within 1-2 days**.  
            - Ensure the task **strictly aligns with the given skills** and evaluates core competencies.  
            - Maintain a **professional tone** and focus on a real-world scenario relevant to the freelancer’s expertise.  
            - The complexity of the task should match the freelancer's skill level:
            - **Beginner** → Basic implementation task  
            - **Intermediate** → Moderate project with some problem-solving involved  
            - **Advanced/Expert** → Complex problem requiring optimization, scalability, or deep technical knowledge  
            - The task should **not require additional setup beyond the specified skills**.  
            - Clearly define the **expected deliverables** and success criteria.  

            **Skills:** {skill_text}  

            **Response Format (JSON):**  
            ```json
            {{
            "task_title": "Short title summarizing the task",
            "task_description": "Detailed description of what the freelancer needs to do",
            "expected_deliverables": [
                "Deliverable 1",
                "Deliverable 2",
                "Deliverable 3"
            ],
            "difficulty_level": "Beginner / Intermediate / Advanced"
            }},
        '''
        
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        
        response_content = response.text if hasattr(response, 'text') else str(response)
        
        json_match = re.search(r'(\{.*\}|\[.*\])', response_content, re.DOTALL)
        
        if json_match:
            json_text = json_match.group(0) 
            parsed_response = json.loads(json_text)
            # formatted_response = format_response_for_readability(parsed_response)
            # return formatted_response
        print(parsed_response)        
        user = UserProfile.objects.get(user_id=user_id)

        serializer = AssignmentResultSerializer(
            data={
                "user_id": user.user_id,
                "assignment_task": str(parsed_response)
            }
        )
        if serializer.is_valid():
            try:
                assignment_question = serializer.save()
            except Exception as e:
                return Response(
                    {"error": f"An error occurred while saving the assignment: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )


        return Response({
        "message": "Task generated successfully",
        "payload": parsed_response,
        "status": 200
        }, status=status.HTTP_200_OK)