from django.urls import path
from .API.talent_registration_views import TalentRegistrationCreateView
from .API.work_experience_views import WorkExperienceCreateView
from .API.education_views import EducationCreateView
from .API.skills_views import SkillsExpertiseCreateView
from .API.job_preferences_views import JobPreferencesCreateView
from .API.preffered_work_views import PreferredWorkTermsCreateView
from .API.portfolio_views import PortfolioReferencesCreateView
from .API.language_views import LanguageProficiencyCreateView
from .API.talent_registration_status import TalentRegistrationStatusView
from .API.talent_make_quiz_views import TalentMakeQuizView
from .API.talent_quiz_result_views import QuizResultCreateView


urlpatterns = [
    path('register/', TalentRegistrationCreateView.as_view(), name='talent_register'),
    path('work-experience/', WorkExperienceCreateView.as_view(), name='work_experience'),
    path('education/', EducationCreateView.as_view(), name='education'),
    path('skills/', SkillsExpertiseCreateView.as_view(), name='skills_expertise'),
    path('job-preferences/', JobPreferencesCreateView.as_view(), name='job_preferences'),
    path('work-terms/', PreferredWorkTermsCreateView.as_view(), name='preferred_work_terms'),
    path('portfolio/', PortfolioReferencesCreateView.as_view(), name='portfolio_references'),
    path('languages/', LanguageProficiencyCreateView.as_view(), name='language_proficiency'),
    path('talent_registration_status/', TalentRegistrationStatusView.as_view(), name='talent_registration_status'),
    path('talent_make_quiz_views/', TalentMakeQuizView.as_view(), name='talent_make_quiz_views'),
    path('talent_quiz_result_views/', QuizResultCreateView.as_view(), name='talent_quiz_result_views'),
]
