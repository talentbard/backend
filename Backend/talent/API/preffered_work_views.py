from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from talent.models import PreferredWorkTerms, TalentRegistrationStatus
from talent.serializers import PreferredWorkTermsSerializer
from user_profile.models import UserProfile

HEADER_PARAMS = {
    'access_token': openapi.Parameter('accesstoken', openapi.IN_HEADER, description="local header param", type=openapi.IN_HEADER),
}

class PreferredWorkTermsCreateView(APIView):
    @swagger_auto_schema(
        operation_description="Save user's preferred work terms.",
        consumes=["application/json"],
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
                    required=["user_id","refresh_token"],
                ),
                "payload": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Preferred work terms details",
                    properties={
                        "work_type": openapi.Schema(
                            type=openapi.TYPE_STRING, 
                            description="Type of work (full_time, part_time, contract, freelance, internship)"
                        ),
                        "availability": openapi.Schema(
                            type=openapi.TYPE_STRING, 
                            description="Availability details"
                        ),
                        "salary_expectation": openapi.Schema(
                            type=openapi.TYPE_STRING, 
                            description="Salary expectation"
                        ),
                        "additional_notes": openapi.Schema(
                            type=openapi.TYPE_STRING, 
                            description="Additional notes"
                        ),
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                    },
                    required=["user_id", "work_type"],
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
                        "work_type": openapi.Schema(type=openapi.TYPE_STRING, description="Work type"),
                        "availability": openapi.Schema(type=openapi.TYPE_STRING, description="Availability"),
                        "salary_expectation": openapi.Schema(type=openapi.TYPE_STRING, description="Salary expectation"),
                        "additional_notes": openapi.Schema(type=openapi.TYPE_STRING, description="Additional notes"),
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
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
        payload = request.data.get("payload", {})

        work_type = payload.get("work_type")
        availability = payload.get("availability")
        salary_expectation = payload.get("salary_expectation")
        additional_notes = payload.get("additional_notes")
        user_id = payload.get("user_id")

        if not work_type or not user_id:
            return Response(
                {"error": "User ID and Work Type are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = UserProfile.objects.get(user_id=user_id)

        serializer = PreferredWorkTermsSerializer(
            data={
                "work_type": work_type,
                "availability": availability,
                "salary_expectation": salary_expectation,
                "additional_notes": additional_notes,
                "user_id": user.user_id,
            }
        )

        if serializer.is_valid():
            work_terms = serializer.save()
            talent_status = TalentRegistrationStatus.objects.get(user_id=user_id)
            talent_status.talent_status = "6"
            talent_status.save()
            user_data = {
                "work_type": work_terms.work_type,
                "availability": work_terms.availability,
                "salary_expectation": work_terms.salary_expectation,
                "additional_notes": work_terms.additional_notes,
                "user_id": str(work_terms.user_id),
            }

            return Response(
                {"message": "Preferred Work Terms added successfully", "user_data": user_data},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
