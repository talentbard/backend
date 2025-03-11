from django.urls import path
from API.skills_expertise_views import SkillsExpertiseCreateView
from API.education_views import EducationCreateView
from API.talent_registration_views import TalentRegistrationCreateView
from API.work_experience_views import WorkExperienceCreateView
from API.portfolio_views import PortfolioReferencesCreateView
from API.preffered_work_views import PreferredWorkTermsCreateView
from API.language_views import LanguageProficiencyCreateView

urlpatterns = [
    path('skills-expertise/', SkillsExpertiseCreateView.as_view(), name='skills-expertise-create'),
]

urlpatterns = [
    path('education/', EducationCreateView.as_view(), name='education-create'),
]

urlpatterns = [
    path('register/', TalentRegistrationCreateView.as_view(), name='talent-register'),
]

urlpatterns = [
    path('work-experience/', WorkExperienceCreateView.as_view(), name='work-experience-create'),
]

urlpatterns = [
    path('portfolio-references/', PortfolioReferencesCreateView.as_view(), name='portfolio-references-create'),
]

urlpatterns = [
    path('preferred-work-terms/', PreferredWorkTermsCreateView.as_view(), name='preferred-work-terms-create'),
]

urlpatterns = [
    path('language-proficiency/', LanguageProficiencyCreateView.as_view(), name='language-proficiency-create'),
]