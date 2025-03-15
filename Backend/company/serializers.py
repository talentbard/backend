from rest_framework import serializers
from .models import CompanyRegistration

class CompanyRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyRegistration
        fields = '__all__'
