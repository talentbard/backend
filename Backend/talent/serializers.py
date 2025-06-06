from rest_framework import serializers
from .models import (
    TalentRegistration, 
    TalentRegistrationStatus, 
    SkillsExpertise, 
    Education, 
    WorkExperience, 
    PortfolioReferences, 
    PreferredWorkTerms, 
    LanguageProficiency, 
    JobPreferences,
    TalentScore,
    AssignmentResult,
    InterviewResult,
    InterviewScheduling,
    TalentExtraInfo,
)

# Talent Registration Serializer
class TalentRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalentRegistration
        fields = '__all__'


# Talent Registration Status Serializer
class TalentRegistrationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalentRegistrationStatus
        fields = '__all__'


# Skills & Expertise Serializer
class SkillsExpertiseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillsExpertise
        fields = '__all__'


# Education Serializer
class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = '__all__'


# Work Experience Serializer
class WorkExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkExperience
        fields = '__all__'


# Portfolio References Serializer
class PortfolioReferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioReferences
        fields = '__all__'


# Preferred Work Terms Serializer
class PreferredWorkTermsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreferredWorkTerms
        fields = '__all__'


# Language Proficiency Serializer
class LanguageProficiencySerializer(serializers.ModelSerializer):
    class Meta:
        model = LanguageProficiency
        fields = '__all__'


# Job Preferences Serializer
class JobPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPreferences
        fields = '__all__'

# Talent Extra Info Serializer
class TalentExtraInfoSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(use_url=True)
    
    class Meta:
        model = TalentExtraInfo
        fields = '__all__'

# Talent Score Serializer
class TalentScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalentScore
        fields = '__all__'

# Assignment Result Serializer
class AssignmentResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentResult
        fields = '__all__'

# Interview Result Serializer
class InterviewResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewResult
        fields = '__all__'

# Interview Decision Serializer
class InterviewSchedulingSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewScheduling
        fields = '__all__'