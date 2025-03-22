from django.db import models
from user_profile.models import UserProfile 

class CompanyRegistration(models.Model):
    FUNDING_CHOICES = [
        ('yes', 'Yes'),
        ('no', 'No'),
    ]

    COMPANY_SIZE_CHOICES = [
        ('1-10', '1-10 employees'),
        ('11-50', '11-50 employees'),
        ('51-200', '51-200 employees'),
        ('201-500', '201-500 employees'),
        ('500+', '500+ employees'),
    ]

    INDUSTRY_CHOICES = [
        ('tech', 'Technology'),
        ('finance', 'Finance'),
        ('healthcare', 'Healthcare'),
        ('education', 'Education'),
        ('marketing', 'Marketing'),
        ('other', 'Other'),
    ]

    BUSINESS_MODEL_CHOICES = [
        ('b2b', 'B2B'),
        ('b2c', 'B2C'),
        ('hybrid', 'Hybrid'),
    ]

    company_name = models.CharField(max_length=255)
    company_phone = models.CharField(max_length=15, null=True, blank=True)
    about_company = models.TextField(null=True, blank=True)
    company_website = models.URLField(null=True, blank=True)
    company_linkedin = models.URLField(null=True, blank=True)
    project_description = models.TextField( null=True, blank=True)
    total_funding_raised = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    designation = models.CharField(max_length=100)
    personal_contact = models.CharField(max_length=20)
    personal_linkedin = models.URLField(null=True, blank=True)
    company_work_email = models.EmailField(unique=True)
    company_size = models.CharField(max_length=20, null=True, blank=True)
    industry = models.CharField(max_length=50, null=True, blank=True)
    sector = models.CharField(max_length=100)
    primary_business_model = models.CharField(max_length=20, null=True, blank=True)
    funding_rounds = models.IntegerField(null=True, blank=True)
    latest_rounds = models.CharField(null=True, blank=True)
    user_id= models.ForeignKey(UserProfile, on_delete=models.CASCADE)  # Link to user
    

    def __str__(self):
        return f"{self.company_name} - {self.user.full_name}"
