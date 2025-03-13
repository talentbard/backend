from rest_framework import serializers
from .models import SkillsExpertise
from .models import Education
from .models import TalentRegistration
from .models import WorkExperience
from .models import PortfolioReferences
from .models import PreferredWorkTerms
from .models import LanguageProficiency
from .models import TalentRegistrationStatus
from .models import JobPreferences



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
    
class WorkExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkExperience
        fields = '__all__'

class PortfolioReferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioReferences
        fields = '__all__'

class PreferredWorkTermsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PreferredWorkTerms
        fields = '__all__'

class LanguageProficiencySerializer(serializers.ModelSerializer):
    class Meta:
        model = LanguageProficiency
        fields = '__all__'

class TalentRegistrationStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalentRegistrationStatus
        fields = '__all__'

class JobPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobPreferences
        fields = '__all__'