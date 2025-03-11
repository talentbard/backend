from django.urls import path
from .skills_views import SkillsExpertiseCreateView
from .edu_views import EducationCreateView
from .talent_views import TalentRegistrationCreateView
from .work_views import WorkExperienceCreateView
from .portfolio_views import PortfolioReferencesCreateView
from .preffered_work_views import PreferredWorkTermsCreateView
from .language_views import LanguageProficiencyCreateView

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