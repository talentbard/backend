from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from talent.models import TalentRegistration, TalentRegistrationStatus
from talent.serializers import TalentRegistrationSerializer
from user_profile.models import UserProfile

HEADER_PARAMS = {
    'access_token': openapi.Parameter(
        'accesstoken', openapi.IN_HEADER, description="JWT access token", type=openapi.TYPE_STRING
    ),
}

class TalentRegistrationCreateView(APIView):
    @swagger_auto_schema(
        operation_description="Register a new talent profile.",
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
                        "full_name": openapi.Schema(type=openapi.TYPE_STRING, description="Full name"),
                        "email_id": openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Email ID"),
                        "phone_no": openapi.Schema(type=openapi.TYPE_STRING, description="Phone number"),
                        "linkedin": openapi.Schema(type=openapi.TYPE_STRING, format="url", description="LinkedIn profile URL"),
                        "current_location": openapi.Schema(type=openapi.TYPE_STRING, description="Current location"),
                        "preferred_location": openapi.Schema(type=openapi.TYPE_STRING, description="Preferred location"),
                        "freelancer_status": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Freelancer status (part_time, full_time, small_studio, other)",
                        ),
                        "availability": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Availability (full_time, part_time, contract, internship)",
                        ),
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                    },
                    required=["user_id", "full_name", "email_id", "freelancer_status", "availability"],
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
                        "full_name": openapi.Schema(type=openapi.TYPE_STRING, description="Full name"),
                        "email_id": openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Email ID"),
                        "phone_no": openapi.Schema(type=openapi.TYPE_STRING, description="Phone number"),
                        "linkedin": openapi.Schema(type=openapi.TYPE_STRING, format="url", description="LinkedIn profile URL"),
                        "current_location": openapi.Schema(type=openapi.TYPE_STRING, description="Current location"),
                        "preferred_location": openapi.Schema(type=openapi.TYPE_STRING, description="Preferred location"),
                        "freelancer_status": openapi.Schema(type=openapi.TYPE_STRING, description="Freelancer status"),
                        "availability": openapi.Schema(type=openapi.TYPE_STRING, description="Availability"),
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
        # import pdb;pdb.set_trace()

        full_name = payload.get("full_name")
        email_id = payload.get("email_id")
        phone_no = payload.get("phone_no")
        linkedin = payload.get("linkedin")
        current_location = payload.get("current_location")
        preferred_location = payload.get("preferred_location")
        freelancer_status = payload.get("freelancer_status")
        availability = payload.get("availability")
        user_id = payload.get("user_id")

        if not full_name or not email_id or not freelancer_status or not availability or not user_id:
            return Response(
                {"error": "User ID, Full Name, Email, Freelancer Status, and Availability are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = UserProfile.objects.get(user_id=user_id)

        serializer = TalentRegistrationSerializer(
            data={
                "full_name": full_name,
                "email_id": email_id,
                "phone_no": phone_no,
                "linkedin": linkedin,
                "current_location": current_location,
                "preferred_location": preferred_location,
                "freelancer_status": freelancer_status,
                "availability": availability,
                "user_id": user.user_id,
            }
        )

        if serializer.is_valid():
            talent_registration = serializer.save()
            # Update Talent Registration Status
            talent_status, _ = TalentRegistrationStatus.objects.get_or_create(user_id=user_id)
            talent_status.status_id = "1" 
            talent_status.save()

            user_data = {
                "full_name": talent_registration.full_name,
                "email_id": talent_registration.email_id,
                "phone_no": talent_registration.phone_no,
                "linkedin": talent_registration.linkedin,
                "current_location": talent_registration.current_location,
                "preferred_location": talent_registration.preferred_location,
                "freelancer_status": talent_registration.freelancer_status,
                "availability": talent_registration.availability
            }

            return Response(
                {"message": "Talent registration successful", "user_data": user_data},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
