from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from user_profile.decorators import authenticate_user_session
from user_profile.models import UserProfile
from talent.models import (
    PreferredWorkTerms,
    TalentRegistrationStatus,
    Education,
    SkillsExpertise,
    WorkExperience,
    PortfolioReferences,
    LanguageProficiency,
    JobPreferences,
    TalentRegistration,
)
from talent.serializers import (
    PreferredWorkTermsSerializer,
    TalentRegistrationStatusSerializer,
    EducationSerializer,
    SkillsExpertiseSerializer,
    WorkExperienceSerializer,
    PortfolioReferencesSerializer,
    LanguageProficiencySerializer,
    JobPreferencesSerializer,
    TalentRegistrationSerializer,
)

HEADER_PARAMS = {
    'access_token': openapi.Parameter('accesstoken', openapi.IN_HEADER, description="local header param", type=openapi.TYPE_STRING),
}

class ProfileCreateView(APIView):
    @swagger_auto_schema(
        operation_description="Get complete talent profile using user ID.",
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
                    description="User payload containing user ID",
                    properties={
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
                        "message": openapi.Schema(type=openapi.TYPE_STRING),
                        "profile": openapi.Schema(type=openapi.TYPE_OBJECT),
                        "status": openapi.Schema(type=openapi.TYPE_INTEGER)
                    },
                ),
            ),
            400: openapi.Response(
                "Bad Request",
                openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    "error": openapi.Schema(type=openapi.TYPE_STRING)
                }),
            ),
            404: openapi.Response(
                "Not Found",
                openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    "error": openapi.Schema(type=openapi.TYPE_STRING)
                }),
            ),
            401: openapi.Response(
                "Unauthorized",
                openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                    "error": openapi.Schema(type=openapi.TYPE_STRING)
                }),
            ),
        },
    )
    @authenticate_user_session
    def post(self, request):
        payload = request.data.get("payload", {})
        user_id = payload.get("user_id")

        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = UserProfile.objects.get(user_id=user_id)
        except UserProfile.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Fetch sections of the talent profile
        education_qs = Education.objects.filter(user_id=user_id)
        work_terms = PreferredWorkTerms.objects.filter(user_id=user_id).first()
        status_talent = TalentRegistrationStatus.objects.filter(user_id=user_id).first()
        skills_qs = SkillsExpertise.objects.filter(user_id=user_id)
        work_exp_qs = WorkExperience.objects.filter(user_id=user_id)
        portfolio_qs = PortfolioReferences.objects.filter(user_id=user_id).first()
        language_qs = LanguageProficiency.objects.filter(user_id=user_id)
        job_pref_qs = JobPreferences.objects.filter(user_id=user_id)
        talent_registration_qs = TalentRegistration.objects.filter(user_id=user_id).first()

        # Serialize sections
        education_data = EducationSerializer(education_qs, many=True).data
        work_terms_data = PreferredWorkTermsSerializer(work_terms).data if work_terms else {}
        status_data = TalentRegistrationStatusSerializer(status_talent).data if status_talent else {}
        skills_data = SkillsExpertiseSerializer(skills_qs, many=True).data
        work_exp_data = WorkExperienceSerializer(work_exp_qs, many=True).data
        portfolio_data = PortfolioReferencesSerializer(portfolio_qs).data if portfolio_qs else {}
        language_data = LanguageProficiencySerializer(language_qs, many=True).data
        job_pref_data = JobPreferencesSerializer(job_pref_qs, many=True).data
        talent_registration_data = TalentRegistrationSerializer(talent_registration_qs).data if talent_registration_qs else {}

        # Construct full profile
        profile = {
            "education": education_data,
            "preferred_work_terms": work_terms_data,
            "talent_status": status_data,
            "skills_expertise": skills_data,
            "work_experience": work_exp_data,
            "portfolio": portfolio_data,
            "languages": language_data,
            "job_preferences": job_pref_data,
            "talent_registration": talent_registration_data,
        }

        return Response(
            {
                "message": "Talent profile retrieved successfully",
                "profile": profile,
                "status": 200
            },
            status=status.HTTP_200_OK
        )
