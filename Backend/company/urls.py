from django.urls import path
from .API.registration_views import CompanyRegistrationCreateView
from .API.company_registration_status import CompanyRegistrationStatusView
from .API.company_profile_views import ProfileCreateView

urlpatterns = [
    path('company_register/', CompanyRegistrationCreateView.as_view(), name='company_register'),
    path('company_registration_status/', CompanyRegistrationStatusView.as_view(), name='company_registration_status'),
    path('company_profile/', ProfileCreateView.as_view(), name='company_profile'),
]