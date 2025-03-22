from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from talent.models import PortfolioReferences, TalentRegistrationStatus
from talent.serializers import PortfolioReferencesSerializer
from user_profile.models import UserProfile
HEADER_PARAMS = {
    'access_token': openapi.Parameter('accesstoken', openapi.IN_HEADER, description="local header param", type=openapi.IN_HEADER),
}

class PortfolioReferencesCreateView(APIView):
    # parser_classes = (MultiPartParser, FormParser)  # Support file uploads

    @swagger_auto_schema(
        operation_description="Save user's portfolio and references.",
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
                    description="Portfolio details",
                    properties={
                        "resume": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BINARY, description="Resume file (optional)"),
                        "project_links": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), description="List of project links"),
                        "references": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), description="List of references"),
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                    },
                    required=["user_id"],
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
                       "resume": openapi.Schema(type=openapi.TYPE_STRING, description="Resume file URL"),
                        "project_links": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), description="List of project links"),
                        "references": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), description="List of references"),
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
        auth_params = request.data.get("auth_params", {})

        resume = payload.get("resume",None)# Handle file uploads
        project_links = payload.get("project_links", [])
        references = payload.get("references", [])
        user_id = payload.get("user_id")

        if not user_id:
            return Response(
                {"error": "User ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = UserProfile.objects.get(user_id=user_id)

        serializer = PortfolioReferencesSerializer(
            data={
                "resume": resume,
                "project_links": project_links,
                "references": references,
                "user_id": user.user_id,
            }
        )

        if serializer.is_valid():
            portfolio = serializer.save()
            talent_status = TalentRegistrationStatus.objects.get(user_id=user_id)
            talent_status.talent_status = "5"  
            talent_status.save()

            user_data = {
                "resume": portfolio.resume.url if portfolio.resume else None,
                "project_links": portfolio.project_links,
                "references": portfolio.references,
            }

            return Response(
                {"message": "Portfolio added successfully", "user_data": user_data},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
