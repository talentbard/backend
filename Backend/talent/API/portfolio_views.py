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

HEADER_PARAMS = {
    'access_token': openapi.Parameter('accesstoken', openapi.IN_HEADER, description="local header param", type=openapi.TYPE_STRING),
}

class PortfolioReferencesCreateView(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def upload_resume_to_supabase(self, file):
        client = get_supabase_client()
        filename = f"resumes/{uuid.uuid4()}_{file.name}"
        file_content = file.read()

        # Upload to Supabase
        response = client.storage.from_('resumes').upload(
            path=filename,
            file=file_content,
            file_options={"content-type": file.content_type}
        )

        # Get public URL
        public_url = client.storage.from_('resumes').get_public_url(filename)
        return public_url

    @swagger_auto_schema(
        operation_description="Upload resume and save portfolio info.",
        manual_parameters=[HEADER_PARAMS['access_token']],
        consumes=["multipart/form-data"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["user_id"],
            properties={
                "resume": openapi.Schema(type=openapi.TYPE_FILE, description="Resume PDF"),
                "project_links": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
                "references": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
                "user_id": openapi.Schema(type=openapi.TYPE_STRING),
                "refresh_token": openapi.Schema(type=openapi.TYPE_STRING),
            }
        ),
        responses={
            200: openapi.Response(description="Success"),
            400: openapi.Response(description="Bad Request"),
            401: openapi.Response(description="Unauthorized"),
            404: openapi.Response(description="User Not Found"),
        }
    )
    @authenticate_user_session
    def post(self, request):
        resume_file = request.FILES.get("resume")
        project_links = request.data.getlist("project_links")
        references = request.data.getlist("references")
        user_id = request.data.get("user_id")

        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = UserProfile.objects.get(user_id=user_id)
        except UserProfile.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Upload resume to Supabase
        resume_url = None
        if resume_file:
            try:
                resume_url = self.upload_resume_to_supabase(resume_file)
            except Exception as e:
                return Response({"error": f"Failed to upload resume: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Save to DB
        serializer = PortfolioReferencesSerializer(data={
            "resume": resume_url,
            "project_links": project_links,
            "references": references,
            "user_id": user.user_id
        })

        if serializer.is_valid():
            portfolio = serializer.save()

            # Update status
            TalentRegistrationStatus.objects.update_or_create(
                user_id=user.user_id,
                defaults={"talent_status": "5"}
            )

            return Response({
                "message": "Portfolio added successfully",
                "user_data": {
                    "resume": resume_url,
                    "project_links": portfolio.project_links,
                    "references": portfolio.references,
                    "user_id": str(user.user_id)
                }
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
