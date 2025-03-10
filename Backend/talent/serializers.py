from rest_framework import serializers
from .models import SkillsExpertise
from .models import Education
from .models import TalentRegistration


class SkillsExpertiseSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillsExpertise
        fields = ['id', 'primary_skill', 'skill_level', 'experience_years', 'secondary_skills', 'certificate_image']

class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = ['id', 'university', 'college_degree', 'field_of_study', 'graduation_date', 'currently_pursuing', 'gpa']

class TalentRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalentRegistration
        fields = '__all__'
    
