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
from .API.talent_make_assignment_views import TalentMakeAssignmentView 
from .API.talent_assignment_result_views import AssignmentResultCreateView
from .API.talent_interview_scheduling_views import InterviewResultCreateView
from .API.talent_profile_views import ProfileCreateView
from .API.interview_get_questions_view import InterviewQuestionsRetrieveView
from .API.interview_questions_view import InterviewQuestionsView
from .API.interview_evaluation_view import InterviewAnswersSaveView



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
    path('talent_make_assignment_views/', TalentMakeAssignmentView.as_view(), name='talent_make_assignment_views'),
    path('talent_assignment_result_views/', AssignmentResultCreateView.as_view(), name='talent_assignment_result_views'),
    path('talent_interview_scheduling_views/', InterviewResultCreateView.as_view(), name='talent_interview_scheduling_views'),
    path('talent_profile_views/', ProfileCreateView.as_view(), name='talent_profile_views'),
    path('interview_questions_generate/', InterviewQuestionsView.as_view(), name='interview_questions_view'),
    path('interview_get_questions_view/', InterviewQuestionsRetrieveView.as_view(), name='interview_get_questions_view'),
    path('interview_evaluation_view/', InterviewAnswersSaveView.as_view(), name='interview_evaluation_view')
]
