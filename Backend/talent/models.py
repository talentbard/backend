import uuid
from datetime import datetime
from django.db import models
from ..user_profile.models import UserProfile

#TalentRegistration
class TalentRegistration(models.Model):
    FREELANCER_STATUS_CHOICES = [
        ("part_time", "Part-time freelancer"),
        ("full_time", "Full-time freelancer"),
        ("small_studio", "Small studio"),
        ("other", "Other"),
    ]
    
    AVAILABILITY_CHOICES = [
        ("full_time", "Full-time"),
        ("part_time", "Part-time"),
        ("contract", "Contract-based"),
        ("internship", "Internship"),
    ]

    full_name = models.CharField(max_length=100, null=False)
    email_id = models.EmailField(max_length=100, unique=True, null=False)
    phone_no = models.CharField(max_length=15, null=True, blank=True)
    linkedin = models.URLField(max_length=200, null=True, blank=True)  # Changed linkdin -> linkedin, made optional
    current_location = models.CharField(max_length=100, null=True, blank=True)
    preferred_location = models.CharField(max_length=100, null=True, blank=True)
    freelancer_status = models.CharField(max_length=20, choices=FREELANCER_STATUS_CHOICES, null=False, default="full_time")
    availability = models.CharField(max_length=20, choices=AVAILABILITY_CHOICES, null=False, default="full_time")
    user_id = models.ForeignKey(UserProfile, default="1", on_delete=models.CASCADE)


    def __str__(self):
        return self.full_name

#Skills & Expertise
class SkillsExpertise(models.Model):
    SKILL_LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('expert', 'Expert'),
    ]

    primary_skill = models.CharField(max_length=100, null=False)  
    skill_level = models.CharField(max_length=20, choices=SKILL_LEVEL_CHOICES, default='beginner')
    experience_years = models.PositiveIntegerField(null=True, blank=True)  # Years of experience
    secondary_skills = models.CharField(max_length=255, null=True, blank=True)  # Comma-separated skills
    certificate_image = models.ImageField(upload_to='certifications/', null=True, blank=True)  # Changed upload path
    user_id = models.ForeignKey(UserProfile, default="1", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.primary_skill} - {self.get_skill_level_display()}"


#Education and Qualifications
class Education(models.Model):
    university = models.CharField(max_length=255, null=False)  # University name
    college_degree = models.CharField(max_length=255, null=False)  # Degree name
    field_of_study = models.CharField(max_length=255, null=True, blank=True)  # Field of Study
    graduation_date = models.DateField(null=True, blank=True)  # Graduation date (User Input)
    currently_pursuing = models.BooleanField(default=False)  # Checkbox for currently pursuing
    gpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)  # GPA max 9.99
    user_id = models.ForeignKey(UserProfile, default="1", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.college_degree} in {self.field_of_study} from {self.university}"

#Work Experience
class WorkExperience(models.Model):
    job_title = models.CharField(max_length=100, null=False)
    company_industry = models.CharField(max_length=150, null=False)
    start_date = models.DateField(null=False)
    end_date = models.DateField(null=True, blank=True)  # Allow blank for ongoing jobs
    responsibilities = models.TextField(null=True, blank=True)
    technologies_used = models.CharField(max_length=200, null=True, blank=True)
    projects = models.TextField(null=True, blank=True)
    user_id = models.ForeignKey(UserProfile, default="1", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.job_title} at {self.company_industry}"
    
#Portfolio and References
class PortfolioReferences(models.Model):
    resume = models.FileField(upload_to='resumes/', null=True, blank=True)
    project_links = models.JSONField(default=list, blank=True)
    references = models.JSONField(default=list, blank=True)
    user_id = models.ForeignKey(UserProfile, default="1", on_delete=models.CASCADE)

    def __str__(self):
        return f"Portfolio (Resume: {self.resume}, Projects: {len(self.project_links)}, References: {len(self.references)})"
    
#Preferred Work Terms
class PreferredWorkTerms(models.Model):
    WORK_TYPE_CHOICES = [
        ('full_time', 'Full-Time'),
        ('part_time', 'Part-Time'),
        ('contract', 'Contract'),
        ('freelance', 'Freelance'),
        ('internship', 'Internship'),
    ]

    work_type = models.CharField(max_length=20, choices=WORK_TYPE_CHOICES)
    availability = models.CharField(max_length=100, null=True, blank=True)
    salary_expectation = models.CharField(max_length=50, null=True, blank=True)
    additional_notes = models.TextField(null=True, blank=True)
    user_id = models.ForeignKey(UserProfile, default="1", on_delete=models.CASCADE)

    def __str__(self):
        return f"Work Type: {self.get_work_type_display()} | Salary: {self.salary_expectation}"
    
#Language Proficiency
class LanguageProficiency(models.Model):
    PROFICIENCY_LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('fluent', 'Fluent'),
        ('native', 'Native'),
    ]

    language = models.CharField(max_length=50)
    proficiency_level = models.CharField(max_length=20, choices=PROFICIENCY_LEVEL_CHOICES)
    certification = models.CharField(max_length=100, null=True, blank=True)
    user_id = models.ForeignKey(UserProfile, default="1", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.language} ({self.get_proficiency_level_display()})"