from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from django.contrib.auth.hashers import make_password, check_password
from talent.models import Education,TalentRegistrationStatus
from talent.serializers import EducationSerializer
from user_profile.models import UserProfile

HEADER_PARAMS = {
    'access_token': openapi.Parameter('accesstoken', openapi.IN_HEADER, description="local header param", type=openapi.IN_HEADER),
}


class EducationCreateView(APIView):
    @swagger_auto_schema(
        operation_description="Save the user's education information using `auth_params`.",
        consumes=["application/json"],
        manual_parameters=[HEADER_PARAMS['access_token']],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "auth_params": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Authentication-related parameters",
                    properties={
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                        "refresh_token": openapi.Schema(type=openapi.TYPE_STRING, description="Refresh token"),
                    },
                    required=["user_id","refresh_token"],
                ),
                "payload": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="User Education details",
                    properties={
                        "university_name": openapi.Schema(type=openapi.TYPE_STRING, description="University Name"),
                        "college_degree": openapi.Schema(type=openapi.TYPE_STRING, description="College Degree"),
                        "field_of_study": openapi.Schema(type=openapi.TYPE_STRING, description="Field of Study "),
                        "graduation_date": openapi.Schema(type=openapi.TYPE_STRING, description="Graduation Date"),
                        "currently_pursuing": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Currently Pursuing"),
                        "gpa": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_DECIMAL, description="College GPA"),
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User id"),

                    },
                    required=["university_name","college_degree","field_of_study","graduation_date","currently_pursuing","gpa","user_id"],
                ),
            },
            required=["payload", "auth_params"],  # `payload` is required
        ),
        responses={
            200: openapi.Response(
                "Success",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "university_name": openapi.Schema(type=openapi.TYPE_STRING, description="University Name"),
                        "college_degree": openapi.Schema(type=openapi.TYPE_STRING, description="College Degree"),
                        "field_of_study": openapi.Schema(type=openapi.TYPE_STRING, description="Field of Study "),
                        "graduation_date": openapi.Schema(type=openapi.TYPE_STRING, description="Graduation Date"),
                        "currently_pursuing": openapi.Schema(type=openapi.TYPE_STRING, description="Currently Pursuing"),
                        "gpa": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_DECIMAL, description="College GPA"),
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User id"),
                    },
                ),
            ),
            400: openapi.Response(
                "Bad Request",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING, description="Error message"),
                    },
                ),
            ),
            404: openapi.Response(
                "User Not Found",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING, description="Error message"),
                    },
                ),
            ),
            401: openapi.Response(
                "Unauthorized",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "error": openapi.Schema(type=openapi.TYPE_STRING, description="Error message"),
                    },
                ),
            ),
        },
    )
    @authenticate_user_session
    def post(self, request):
        payload = request.data.get('payload', {})
        university_name = payload.get('university_name')
        college_degree = payload.get('college_degree')
        field_of_study = payload.get('field_of_study')
        graduation_date = payload.get('graduation_date')
        currently_pursuing = payload.get('currently_pursuing')
        gpa = payload.get('gpa')
        user_id = payload.get('user_id')


        if not university_name or not college_degree or not field_of_study or not graduation_date or not gpa: #doubt currently_pursuing
            return Response(
                {"error": "University name, college degree, feild of study, graduation date and gpa are required in the payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = UserProfile.objects.get(user_id=user_id)

        serializer = EducationSerializer(
            data={
                "university": university_name,
                "college_degree": college_degree,
                "field_of_study": field_of_study,
                "graduation_date": graduation_date,
                "currently_pursuing": currently_pursuing,
                "gpa": gpa,
                "user_id": user.user_id,
            }
        )
        if serializer.is_valid():
            user = serializer.save()
            # Retrieve the object by user_id
            talent_status = TalentRegistrationStatus.objects.get(user_id=user_id)
            # Update talent_status
            talent_status.talent_status = "3"
            # Save the changes
            talent_status.save()
            user_data = {
                "university_name": user.university,
                "college_degree": user.college_degree,
                "field_of_study": user.field_of_study,
                "graduation_date": user.graduation_date,
                "currently_pursuing": user.currently_pursuing,
                "gpa": user.gpa,

            }

            return Response(
                {"message": "User registered successfully", "user_data": user_data},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
