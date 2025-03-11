from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status, generics
from .models import WorkExperience
from .serializers import WorkExperienceSerializer

class WorkExperienceCreateView(generics.CreateAPIView):
    queryset = WorkExperience.objects.all()
    serializer_class = WorkExperienceSerializer