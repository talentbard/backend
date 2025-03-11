from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status, generics
from ..models import TalentRegistration
from ..serializers import TalentRegistrationSerializer

class TalentRegistrationCreateView(generics.CreateAPIView):
    queryset = TalentRegistration.objects.all()
    serializer_class = TalentRegistrationSerializer