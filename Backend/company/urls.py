from django.urls import path
from company.views import CompanyRegistrationCreateView

urlpatterns = [
    path('company_register/', CompanyRegistrationCreateView.as_view(), name='company_register'),
]