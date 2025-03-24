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
    QuizResult
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

#Quiz Result Serializer
class QuizResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizResult
        fields = '__all__'