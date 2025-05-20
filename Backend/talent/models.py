import uuid
from datetime import datetime
from django.db import models
from user_profile.models import UserProfile
from django.contrib.postgres.fields import ArrayField

class TalentRegistrationStatus(models.Model):
    status_id = models.CharField(default="0", max_length=100)
    talent_status = models.CharField(default="0", max_length=100)
    user_id = models.ForeignKey(UserProfile, default="1", on_delete=models.CASCADE)

    def __str__(self):
        return self.status_id
    
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
    freelancer_status = models.CharField(max_length=20, null=False, default="full_time")
    availability = models.CharField(max_length=20, null=False, default="full_time")
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

    primary_skills = models.JSONField(default=list)
    secondary_skills = models.JSONField(default=list, blank=True, null=True)  # Comma-separated skills
    certificate_images = models.JSONField(default=list, blank=True, null=True)
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
    company = models.CharField(max_length=150, null=False)
    industry = models.CharField(max_length=150, null=False)
    start_date = models.DateField(null=False)
    end_date = models.DateField(null=True, blank=True)  # Allow blank for ongoing jobs
    responsibilities = models.TextField(null=True, blank=True)
    achievements = models.TextField(null=True, blank=True)
    technologies_used = models.CharField(max_length=200, null=True, blank=True)
    projects = models.TextField(null=True, blank=True)
    user_id = models.ForeignKey(UserProfile, on_delete=models.CASCADE,db_column="user_id")  # Linking to user

    def __str__(self):
        return f"{self.job_title} at {self.company}"
    
#Portfolio and References
class PortfolioReferences(models.Model):
    resume = models.TextField(null=True, blank=True)
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

    work_type = models.CharField(max_length=20,null = False)
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
    proficiency_level = models.CharField(max_length=20, null = False)
    certification = models.CharField(max_length=100, null=True, blank=True)
    user_id = models.ForeignKey(UserProfile, default="1", on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.language} ({self.get_proficiency_level_display()})"
    
#Job Preference
class JobPreferences(models.Model):
    user_id = models.ForeignKey(UserProfile, on_delete=models.CASCADE)  # Link to user
    job_title = models.CharField(max_length=100, null=False)
    preferred_job_type = models.CharField(max_length=20,null=False)
    industry = models.CharField(max_length=50, null=False)
    desired_role = models.CharField(max_length=100, null=True, blank=True)
    career_objective = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.job_title} - {self.user}"

#Quiz Generation
class TalentScore(models.Model):
    score_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_id = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    quiz_score = models.IntegerField(null=True,blank=True)
    assignment_score = models.IntegerField(null=True,blank=True)
    interview_score = models.IntegerField(null=True,blank=True)
    work_score = models.CharField(null=True,blank=True)
    grade = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.score_id
    
#Assignment Generation
class AssignmentResult(models.Model):
    assignment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment_task = models.TextField(null=True, blank=True)
    assignment_submission = models.TextField(null=True, blank=True)
    assignment_score = models.CharField(null=True, blank=True)
    user_id = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    def __str__(self):
        return self.assignment_id
    
# Interview Scheduling
class InterviewResult(models.Model):
    interview_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    interview_done = models.BooleanField(default=False)
    interview_scheduled = models.DateTimeField(null=True, blank=True)
    interview_score = models.CharField(null=True, blank=True)
    user_id = models.ForeignKey(UserProfile, on_delete=models.CASCADE)

    def __str__(self):
        return self.interview_id
    
class InterviewQuestion(models.Model):
    interview_questions_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='interview_questions')
    questions = models.JSONField(default=list, help_text="List of 10 interview questions in JSON format")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when questions were generated")

    def __str__(self):
        return str(self.interview_questions_id)
    

class InterviewAnswer(models.Model):
    interview_answer_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='interview_answers')
    question_answers = models.JSONField(default=list, help_text="List of question-answer pairs with evaluation in JSON format")
    score = models.FloatField(null=True, blank=True, help_text="Evaluation score out of 100")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when answers were submitted")

    def __str__(self):
        return f"Interview Answers for User {self.user_id} (ID: {self.interview_answer_id}, Score: {self.score})"