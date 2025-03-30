from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from django.contrib.auth.hashers import make_password, check_password
from user_profile.models import UserProfile
from talent.models import InterviewResult, TalentRegistrationStatus
from talent.serializers import InterviewResultSerializer

HEADER_PARAMS = {
    'access_token': openapi.Parameter('accesstoken', openapi.IN_HEADER, description="local header param", type=openapi.IN_HEADER),
}

class InterviewResultCreateView(APIView):
    @swagger_auto_schema(
        operation_description="Save the user's interview details`.",
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
                        "interview_scheduled": openapi.Schema(type=openapi.TYPE_STRING, description="Interview Scheduling"),
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                    },
                    required=["interview_scheduled","user_id"],
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
                        "interview_scheduled": openapi.Schema(type=openapi.TYPE_STRING, description="Interview Scheduling"),
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
        payload = request.data.get('payload', {})
        interview_scheduled = payload.get('interview_scheduled')
        user_id = payload.get('user_id')


        if not user_id or not interview_scheduled: #doubt currently_pursuing
            return Response(
                {"error": " interview_scheduled, user id are required in the payload."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = UserProfile.objects.get(user_id=user_id)

        serializer = InterviewResultSerializer(
            data={
                "interview_scheduled": interview_scheduled,
                "user_id": user.user_id,
            }
        )
        if serializer.is_valid():
            user = serializer.save()
            # Retrieve the object by user_id
            talent_status = TalentRegistrationStatus.objects.get(user_id=user_id)
            # Update talent_status
            talent_status.talent_status = "11"
            # Save the changes
            talent_status.save()
            user_data = {
                "interview_scheduled": user.interview_scheduled,

            }

            return Response(
                {"message": "User intervie scheduled successfully", "user_data": user_data},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
