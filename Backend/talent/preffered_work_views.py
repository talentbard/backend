from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status, generics
from .models import PreferredWorkTerms
from .serializers import PreferredWorkTermsSerializer

class PreferredWorkTermsCreateView(generics.CreateAPIView):
    queryset = PreferredWorkTerms.objects.all()
    serializer_class = PreferredWorkTermsSerializer