from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from company.models import CompanyRegistration
from company.serializers import CompanyRegistrationSerializer
from talent.models import TalentRegistrationStatus
from user_profile.models import UserProfile

HEADER_PARAMS = {
    'access_token': openapi.Parameter(
        'accesstoken', openapi.IN_HEADER, description="JWT access token", type=openapi.TYPE_STRING
    ),
}

class CompanyRegistrationCreateView(APIView):
    @swagger_auto_schema(
        operation_description="Register a new company.",
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
                    description="Company registration details",
                    properties={
                        "company_name": openapi.Schema(type=openapi.TYPE_STRING, description="Company name"),
                        "company_phone": openapi.Schema(type=openapi.TYPE_STRING, description="Company phone number"),
                        "about_company": openapi.Schema(type=openapi.TYPE_STRING, description="About the company"),
                        "company_website": openapi.Schema(type=openapi.TYPE_STRING, format="url", description="Company website"),
                        "company_linkedin": openapi.Schema(type=openapi.TYPE_STRING, format="url", description="Company LinkedIn profile"),
                        "project_description": openapi.Schema(type=openapi.TYPE_STRING, description="Project description"),
                        "total_funding_raised": openapi.Schema(type=openapi.TYPE_NUMBER, format="decimal", description="Total funding raised"),
                        "designation": openapi.Schema(type=openapi.TYPE_STRING, description="Your designation in the company"),
                        "personal_contact": openapi.Schema(type=openapi.TYPE_STRING, description="Personal contact number"),
                        "personal_linkedin": openapi.Schema(type=openapi.TYPE_STRING, format="url", description="Personal LinkedIn profile"),
                        "company_work_email": openapi.Schema(type=openapi.TYPE_STRING, format="email", description="Company work email"),
                        "company_size": openapi.Schema(type=openapi.TYPE_STRING, description="Company size"),
                        "industry": openapi.Schema(type=openapi.TYPE_STRING, description="Industry"),
                        "sector": openapi.Schema(type=openapi.TYPE_STRING, description="Company sector"),
                        "primary_business_model": openapi.Schema(type=openapi.TYPE_STRING, description="Primary business model"),
                        "funding_raised": openapi.Schema(type=openapi.TYPE_STRING, description="Funding raised (yes/no)"),
                        "funding_rounds": openapi.Schema(type=openapi.TYPE_INTEGER, description="Funding rounds"),
                        "latest_rounds": openapi.Schema(type=openapi.TYPE_STRING, description="Latest funding rounds"),
                        "user_id": openapi.Schema(type=openapi.TYPE_STRING, description="User ID"),
                    },
                    required=["company_name", "company_phone", "about_company", "designation", "personal_contact", "company_work_email", "company_size", "industry", "sector", "primary_business_model", "user_id"],
                ),
            },
            required=["payload", "auth_params"],
        ),
        responses={
            201: openapi.Response("Success", CompanyRegistrationSerializer),
            400: openapi.Response("Bad Request", openapi.Schema(type=openapi.TYPE_OBJECT, properties={"error": openapi.Schema(type=openapi.TYPE_STRING)})),
            404: openapi.Response("User Not Found", openapi.Schema(type=openapi.TYPE_OBJECT, properties={"error": openapi.Schema(type=openapi.TYPE_STRING)})),
            401: openapi.Response("Unauthorized", openapi.Schema(type=openapi.TYPE_OBJECT, properties={"error": openapi.Schema(type=openapi.TYPE_STRING)})),
        },
    )
    @authenticate_user_session
    def post(self, request):
        payload = request.data.get("payload", {})
        
        company_name = payload.get("company_name")
        company_phone = payload.get("company_phone")
        about_company = payload.get("about_company")
        company_website = payload.get("company_website")
        company_linkedin = payload.get("company_linkedin")
        project_description = payload.get("project_description")
        total_funding_raised = payload.get("total_funding_raised")
        designation = payload.get("designation")
        personal_contact = payload.get("personal_contact")
        personal_linkedin = payload.get("personal_linkedin")
        company_work_email = payload.get("company_work_email")
        company_size = payload.get("company_size")
        industry = payload.get("industry")
        sector = payload.get("sector")
        primary_business_model = payload.get("primary_business_model")
        funding_raised = payload.get("funding_raised")
        funding_rounds = payload.get("funding_rounds")
        latest_rounds = payload.get("latest_rounds")
        user_id = payload.get("user_id")

        if not company_name or not company_phone or not about_company or not designation or not personal_contact or not company_work_email or not company_size or not industry or not sector or not primary_business_model or not user_id:
            return Response(
                {"error": "Required fields are missing."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = UserProfile.objects.get(user_id=user_id)

        serializer = CompanyRegistrationSerializer(
            data={
                "company_name": company_name,
                "company_phone": company_phone,
                "about_company": about_company,
                "company_website": company_website,
                "company_linkedin": company_linkedin,
                "project_description": project_description,
                "total_funding_raised": total_funding_raised,
                "designation": designation,
                "personal_contact": personal_contact,
                "personal_linkedin": personal_linkedin,
                "company_work_email": company_work_email,
                "company_size": company_size,
                "industry": industry,
                "sector": sector,
                "primary_business_model": primary_business_model,
                "funding_raised": funding_raised,
                "funding_rounds": funding_rounds,
                "latest_rounds": latest_rounds,
                "user_id": user.user_id,

            }
        )

        if serializer.is_valid():
            company = serializer.save()
            talent_status = TalentRegistrationStatus.objects.get(user_id=user_id)
            # Update talent_status
            talent_status.talent_status = "1"
            # Save the changes
            talent_status.save()
            return Response(
                {"message": "Company registered successfully", "company_data": serializer.data},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
