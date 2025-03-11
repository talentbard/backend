from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status, generics
from .models import Education
from .serializers import EducationSerializer

class EducationCreateView(generics.CreateAPIView):
    queryset = Education.objects.all()
    serializer_class = EducationSerializer