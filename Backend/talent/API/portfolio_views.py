from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from user_profile.models import UserProfile
from talent.models import PortfolioReferences, TalentRegistrationStatus
from talent.serializers import PortfolioReferencesSerializer
from supabase_client import get_supabase_client
import uuid
import logging
import json

# Configure logging
logger = logging.getLogger(__name__)

HEADER_PARAMS = {
    'access_token': openapi.Parameter('accesstoken', openapi.IN_HEADER, description="JWT access token", type=openapi.TYPE_STRING),
}

class PortfolioReferencesCreateView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def upload_resume_to_supabase(self, file, user_id):
        try:
            client = get_supabase_client()
            filename = f"resumes/{uuid.uuid4()}_{file.name}"
            file_content = file.read()

            logger.info(f"Uploading resume for user {user_id} to Supabase: {filename}")
            response = client.storage.from_('resumes').upload(
                path=filename,
                file=file_content,
                file_options={"content-type": file.content_type}
            )

            public_url = client.storage.from_('resumes').get_public_url(filename)
            logger.info(f"Resume uploaded successfully, public URL: {public_url}")
            return public_url
        except Exception as e:
            logger.error(f"Failed to upload resume for user {user_id}: {str(e)}")
            raise

    @swagger_auto_schema(
        operation_description="Upload resume and save portfolio references.",
        manual_parameters=[HEADER_PARAMS['access_token']],
        consumes=["multipart/form-data"],
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
                        "resume": openapi.Schema(type=openapi.TYPE_FILE, description="Resume PDF"),
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
                    logger.error("Invalid JSON in auth_params")
                    return Response({"error": "Invalid auth_params format"}, status=status.HTTP_400_BAD_REQUEST)

            payload = request.data.get("payload", {})
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON in payload")
                    return Response({"error": "Invalid payload format"}, status=status.HTTP_400_BAD_REQUEST)

            user_id = auth_params.get("user_id")
            resume_file = request.FILES.get("resume")
            project_links = payload.get("project_links", [])
            references = payload.get("references", [])

            logger.info(f"Processing portfolio for user_id: {user_id}")

            # Validate inputs
            if not user_id:
                logger.error("User ID missing in auth_params")
                return Response({"error": "User ID is required"}, status=status.HTTP_400_BAD_REQUEST)

            if not resume_file:
                logger.error("Resume file missing")
                return Response({"error": "Resume file is required"}, status=status.HTTP_400_BAD_REQUEST)

            # Validate user
            try:
                user = UserProfile.objects.get(user_id=user_id)
            except UserProfile.DoesNotExist:
                logger.error(f"User not found: {user_id}")
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

            # Upload resume to Supabase
            resume_url = None
            try:
                resume_url = self.upload_resume_to_supabase(resume_file, user_id)
            except Exception as e:
                return Response({"error": f"Failed to upload resume: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Ensure project_links and references are lists
            try:
                project_links = json.loads(project_links) if isinstance(project_links, str) else project_links
                references = json.loads(references) if isinstance(references, str) else references
                if not isinstance(project_links, list) or not isinstance(references, list):
                    raise ValueError("project_links and references must be lists")
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Invalid format for project_links or references: {str(e)}")
                return Response({"error": "project_links and references must be valid JSON arrays"}, status=status.HTTP_400_BAD_REQUEST)

            # Serialize and save portfolio
            serializer = PortfolioReferencesSerializer(data={
                "resume": resume_url,
                "project_links": project_links,
                "references": references,
                "user_id": user.user_id
            })

            if serializer.is_valid():
                try:
                    portfolio = serializer.save()
                    logger.info(f"Portfolio saved for user {user_id}: {portfolio.id}")

                    # Update talent status
                    try:
                        TalentRegistrationStatus.objects.update_or_create(
                            user_id=user,
                            defaults={"talent_status": "5"}
                        )
                        logger.info(f"Talent status updated for user {user_id}")
                    except Exception as e:
                        logger.error(f"Failed to update talent status for user {user_id}: {str(e)}")
                        return Response({"error": f"Failed to update talent status: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                    return Response({
                        "message": "Portfolio added successfully",
                        "user_data": {
                            "resume": resume_url,
                            "project_links": portfolio.project_links,
                            "references": portfolio.references,
                            "user_id": str(user.user_id)
                        }
                    }, status=status.HTTP_201_CREATED)
                except Exception as e:
                    logger.error(f"Failed to save portfolio for user {user_id}: {str(e)}")
                    return Response({"error": f"Failed to save portfolio: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                logger.error(f"Serializer errors for user {user_id}: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Unexpected error in PortfolioReferencesCreateView for user_id {user_id}: {str(e)}")
            return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)