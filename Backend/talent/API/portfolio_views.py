from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from user_profile.models import UserProfile
from talent.models import PortfolioReferences, TalentRegistrationStatus
from talent.serializers import PortfolioReferencesSerializer
import json

HEADER_PARAMS = {
    'access_token': openapi.Parameter('accesstoken', openapi.IN_HEADER, description="JWT access token", type=openapi.TYPE_STRING),
}

class PortfolioReferencesCreateView(APIView):
    @swagger_auto_schema(
        operation_description="Save portfolio references with resume text provided by the frontend.",
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
                    description="Portfolio details",
                    properties={
                        "resume": openapi.Schema(type=openapi.TYPE_STRING, description="Resume text"),
                        "project_links": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
                        "references": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
                    },
                    required=["resume"],
                ),
            },
            required=["auth_params", "payload"],
        ),
        responses={
            201: openapi.Response(description="Created"),
            400: openapi.Response(description="Bad Request"),
            401: openapi.Response(description="Unauthorized"),
            404: openapi.Response(description="User Not Found"),
            500: openapi.Response(description="Internal Server Error"),
        }
    )
    @authenticate_user_session
    def post(self, request):
        try:
            # Parse auth_params and payload
            auth_params = request.data.get("auth_params", {})
            if isinstance(auth_params, str):
                try:
                    auth_params = json.loads(auth_params)
                except json.JSONDecodeError:
                    return Response({"error": "Invalid auth_params JSON format"}, status=status.HTTP_400_BAD_REQUEST)

            payload = request.data.get("payload", {})
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    return Response({"error": "Invalid payload JSON format"}, status=status.HTTP_400_BAD_REQUEST)

            user_id = auth_params.get("user_id")
            resume_text = payload.get("resume")
            project_links = payload.get("project_links", [])
            references = payload.get("references", [])

            if not user_id:
                return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)

            if not resume_text:
                return Response({"error": "Resume text is required"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = UserProfile.objects.get(user_id=user_id)
            except UserProfile.DoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            # Ensure project_links and references are lists
            if isinstance(project_links, str):
                try:
                    project_links = json.loads(project_links)
                except json.JSONDecodeError:
                    return Response({"error": "Invalid project_links JSON format"}, status=status.HTTP_400_BAD_REQUEST)
            if isinstance(references, str):
                try:
                    references = json.loads(references)
                except json.JSONDecodeError:
                    return Response({"error": "Invalid references JSON format"}, status=status.HTTP_400_BAD_REQUEST)

            serializer = PortfolioReferencesSerializer(data={
                "resume": resume_text,
                "project_links": project_links,
                "references": references,
                "user_id": user.id  # Use UserProfile instance ID
            })

            if serializer.is_valid():
                try:
                    portfolio = serializer.save()
                    try:
                        talent_status, _ = TalentRegistrationStatus.objects.get_or_create(user_id=user_id)
                        talent_status.status_id = "5"
                        talent_status.save()
                    except Exception as e:
                        return Response({"error": f"Failed to update talent status: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                    return Response({
                        "message": "Portfolio added successfully",
                        "user_data": {
                            "resume": resume_text,
                            "project_links": portfolio.project_links,
                            "references": portfolio.references,
                            "user_id": str(user.user_id)
                        }
                    }, status=status.HTTP_201_CREATED)
                except Exception as e:
                    return Response({"error": f"Failed to save portfolio: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return Response({"error": f"Serializer validation failed: {serializer.errors}"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": f"Internal server error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)