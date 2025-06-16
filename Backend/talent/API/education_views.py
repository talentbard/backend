from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from talent.models import Education, TalentRegistrationStatus
from user_profile.models import UserProfile
from datetime import datetime

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
                    required=["user_id", "refresh_token"],
                ),
                "payload": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="User Education details",
                    properties={
                        "university_name": openapi.Schema(type=openapi.TYPE_STRING, description="University Name"),
                        "college_degree": openapi.Schema(type=openapi.TYPE_STRING, description="College Degree"),
                        "field_of_study": openapi.Schema(type=openapi.TYPE_STRING, description="Field of Study"),
                        "graduation_date": openapi.Schema(type=openapi.TYPE_STRING, description="Graduation Date (YYYY-MM-DD)"),
                        "currently_pursuing": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Currently Pursuing"),
                        "gpa": openapi.Schema(type=openapi.TYPE_NUMBER, format=openapi.FORMAT_DECIMAL, description="College GPA"),
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User id"),
                    },
                    required=["university_name", "college_degree", "field_of_study", "currently_pursuing", "gpa", "user_id"],
                ),
            },
            required=["payload", "auth_params"],
        ),
        responses={
            200: openapi.Response("Success"),
            400: openapi.Response("Bad Request"),
            404: openapi.Response("User Not Found"),
            401: openapi.Response("Unauthorized"),
        },
    )

    @authenticate_user_session
    def post(self, request):
        try:
            payload = request.data.get('payload', {})
            university_name = payload.get('university_name')
            college_degree = payload.get('college_degree')
            field_of_study = payload.get('field_of_study')
            graduation_date = payload.get('graduation_date')
            currently_pursuing = payload.get('currently_pursuing')
            gpa = payload.get('gpa')
            user_id = payload.get('user_id')

            # Validate required fields
            if not university_name or not college_degree or not field_of_study or gpa is None:
                return Response(
                    {"error": "University name, college degree, field of study, and gpa are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Graduation date validation logic
            if currently_pursuing is True:
                graduation_date = None
            else:
                if not graduation_date:
                    return Response(
                        {"error": "Graduation date is required if not currently pursuing."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                try:
                    graduation_date = datetime.strptime(graduation_date, "%Y-%m-%d").date()
                except ValueError:
                    return Response(
                        {"error": "Graduation date must be in YYYY-MM-DD format."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            try:
                user = UserProfile.objects.get(user_id=user_id)
            except UserProfile.DoesNotExist:
                return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

            # Safely handle duplicates: update if exists else create
            education_instance = Education.objects.filter(user_id=user).first()

            if education_instance:
                # Update existing education
                education_instance.university = university_name
                education_instance.college_degree = college_degree
                education_instance.field_of_study = field_of_study
                education_instance.graduation_date = graduation_date
                education_instance.currently_pursuing = currently_pursuing
                education_instance.gpa = gpa
                education_instance.save()
            else:
                # Create new education
                education_instance = Education.objects.create(
                    university=university_name,
                    college_degree=college_degree,
                    field_of_study=field_of_study,
                    graduation_date=graduation_date,
                    currently_pursuing=currently_pursuing,
                    gpa=gpa,
                    user_id=user,
                )

            # Update talent registration status if exists
            talent_status = TalentRegistrationStatus.objects.filter(user_id=user).first()
            if talent_status:
                talent_status.status_id = "3"
                talent_status.save()

            # Prepare response data
            user_data = {
                "university_name": education_instance.university,
                "college_degree": education_instance.college_degree,
                "field_of_study": education_instance.field_of_study,
                "graduation_date": education_instance.graduation_date,
                "currently_pursuing": education_instance.currently_pursuing,
                "gpa": education_instance.gpa,
            }

            return Response(
                {"message": "Education data saved successfully.", "user_data": user_data},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {"error": "An unexpected error occurred.", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
