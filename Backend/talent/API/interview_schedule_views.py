from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.models import UserProfile
from talent.models import TalentRegistrationStatus, InterviewScheduling
from user_profile.decorators import authenticate_user_session

HEADER_PARAMS = {
    'access_token': openapi.Parameter(
        'accesstoken', openapi.IN_HEADER,
        description="JWT access token",
        type=openapi.TYPE_STRING
    ),
}

class InterviewDecisionView(APIView):
    @swagger_auto_schema(
        operation_description="Admin sets final interview decision for a talent (pass/fail).",
        manual_parameters=[HEADER_PARAMS['access_token']],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["admin_key", "user_id", "status_id"],
            properties={
                "admin_key": openapi.Schema(type=openapi.TYPE_STRING, description="Admin key for authentication"),
                "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="Talent user ID"),
                "status_id": openapi.Schema(type=openapi.TYPE_STRING, description="Status ID: '13' (Selected), '14' (Rejected)"),
                "remark": openapi.Schema(type=openapi.TYPE_STRING, description="Optional remark from admin"),
            },
        ),
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "user_data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "user_id": openapi.Schema(type=openapi.TYPE_STRING),
                                "status_id": openapi.Schema(type=openapi.TYPE_STRING),
                                "interview_result": openapi.Schema(type=openapi.TYPE_STRING),
                            },
                        ),
                    },
                )
            ),
            400: openapi.Response(description="Bad Request"),
            403: openapi.Response(description="Forbidden - Invalid Admin Key"),
            404: openapi.Response(description="User Not Found"),
            500: openapi.Response(description="Internal Server Error"),
        },
    )
    @authenticate_user_session
    def post(self, request):
        data = request.data

        admin_key = data.get("admin_key")
        user_id = data.get("user_id")
        status_id = data.get("status_id")
        remark = data.get("remark", "")

        # Validate required fields
        if not admin_key or not user_id or not status_id:
            return Response({"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST)

        if admin_key != "demo":
            return Response({"error": "Invalid admin key"}, status=status.HTTP_403_FORBIDDEN)

        # Fetch talent user
        try:
            user = UserProfile.objects.get(user_id=user_id)
        except UserProfile.DoesNotExist:
            return Response({"error": "Talent user not found"}, status=status.HTTP_404_NOT_FOUND)

        if status_id not in ["13", "14"]:
            return Response({"error": "Invalid status_id. Must be '13' or '14'"}, status=status.HTTP_400_BAD_REQUEST)

        # Update TalentRegistrationStatus
        try:
            talent_status, _ = TalentRegistrationStatus.objects.get_or_create(user_id=user)
            talent_status.status_id = status_id
            talent_status.save()
        except Exception as e:
            return Response({"error": f"Failed to update status: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Update InterviewScheduling if it exists, or create a record
        try:
            interview = InterviewScheduling.objects.filter(user=user).latest("scheduled_datetime")
            interview.status = "completed"
            interview.is_selected = (status_id == "13")
            interview.remark = remark
            interview.save()
        except InterviewScheduling.DoesNotExist:
            try:
                InterviewScheduling.objects.create(
                    user=user,
                    scheduled_datetime=None,  # ⚠️ Optional: Adjust if DB does not allow null
                    status="completed",
                    is_selected=(status_id == "13"),
                    remark=remark
                )
            except Exception as e:
                return Response({"error": f"Failed to log interview: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(
            {
                "message": "Interview decision updated successfully",
                "user_data": {
                    "user_id": user.user_id,
                    "status_id": status_id,
                    "interview_result": "Selected" if status_id == "13" else "Rejected"
                },
            },
            status=status.HTTP_200_OK
        )
