from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status, generics
from ..models import SkillsExpertise
from ..serializers import SkillsExpertiseSerializer

class SkillsExpertiseCreateView(generics.CreateAPIView):
    queryset = SkillsExpertise.objects.all()
    serializer_class = SkillsExpertiseSerializer
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)