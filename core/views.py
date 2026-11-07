import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    permission_classes = []          # allow anyone
    authentication_classes = []

    def get(self, request, *args, **kwargs):
        logger.debug("Health check called")
        return Response({"status": "ok"}, status=status.HTTP_200_OK)