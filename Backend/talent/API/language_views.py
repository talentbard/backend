from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status, generics
from ..models import LanguageProficiency
from ..serializers import LanguageProficiencySerializer

class LanguageProficiencyCreateView(generics.CreateAPIView):
    queryset = LanguageProficiency.objects.all()
    serializer_class = LanguageProficiencySerializer