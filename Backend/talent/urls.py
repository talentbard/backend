from django.urls import path
from talent.API.skills_expertise_views import SkillsExpertiseCreateView
from talent.API.education_views import EducationCreateView
from talent.API.talent_registration_views import TalentRegistrationCreateView
from talent.API.work_experience_views import WorkExperienceCreateView
from talent.API.portfolio_views import PortfolioReferencesCreateView
from talent.API.preffered_work_views import PreferredWorkTermsCreateView
from talent.API.language_views import LanguageProficiencyCreateView
from talent.API.job_preferences_views import JobPreferencesCreateView


urlpatterns = [
    path('skills-expertise/', SkillsExpertiseCreateView.as_view(), name='skills-expertise-create'),
    path('education/', EducationCreateView.as_view(), name='education-create'),
    path('register/', TalentRegistrationCreateView.as_view(), name='talent-register'),
    path('work-experience/', WorkExperienceCreateView.as_view(), name='work-experience-create'),
    path('portfolio-references/', PortfolioReferencesCreateView.as_view(), name='portfolio-references-create'),
    path('preferred-work-terms/', PreferredWorkTermsCreateView.as_view(), name='preferred-work-terms-create'),
    path('language-proficiency/', LanguageProficiencyCreateView.as_view(), name='language-proficiency-create'),
    path('job-preferences/', JobPreferencesCreateView.as_view(), name='language-proficiency-create'),

]