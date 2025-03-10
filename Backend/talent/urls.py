from django.urls import path
from .views import SkillsExpertiseCreateView
from .views import EducationCreateView
from .views import TalentRegistrationCreateView


urlpatterns = [
    path('skills-expertise/', SkillsExpertiseCreateView.as_view(), name='skills-expertise-create'),
]

urlpatterns = [
    path('education/', EducationCreateView.as_view(), name='education-create'),
]

urlpatterns = [
    path('register/', TalentRegistrationCreateView.as_view(), name='talent-register'),
]