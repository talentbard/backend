from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status, generics
from .models import PortfolioReferences
from .serializers import PortfolioReferencesSerializer

class PortfolioReferencesCreateView(generics.CreateAPIView):
    queryset = PortfolioReferences.objects.all()
    serializer_class = PortfolioReferencesSerializer