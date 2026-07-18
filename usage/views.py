import logging

from drf_spectacular.utils import OpenApiExample
from drf_spectacular.utils import OpenApiResponse
from drf_spectacular.utils import extend_schema

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import DataRequestSerializer
from .services import UsageService

logger = logging.getLogger(__name__)


class DataAPIView(APIView):
    """
    Public endpoint that tenants call to receive data.
    Every successful request is automatically metered.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Retrieve data from an API endpoint",
        description=(
            "Returns sample data and automatically records "
            "API usage for billing."
        ),
        request=DataRequestSerializer,
        responses={
            200: OpenApiResponse(description="Data returned successfully"),
            400: OpenApiResponse(description="Validation error"),
            404: OpenApiResponse(description="Endpoint not found"),
        },
        examples=[
            OpenApiExample(
                "Example Request",
                value={
                    "endpoint_path": "/weather/",
                },
                request_only=True,
            )
        ],
        tags=["Usage"],
    )
    def post(self, request):

        serializer = DataRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        endpoint = UsageService.get_active_endpoint(
            tenant=request.user.tenant,
            endpoint_path=serializer.validated_data["endpoint_path"],
        )


        payload = {
            "temperature": 22,
            "humidity": 65,
            "status": "Sunny",
        }

        data_bytes = len(str(payload).encode("utf-8"))

        UsageService.record_usage(
            tenant=request.user.tenant,
            user=request.user,
            endpoint=endpoint,
            calls=1,
            data_bytes=data_bytes,
        )

        logger.info(
            "Data served | tenant=%s endpoint=%s user=%s",
            request.user.tenant.slug,
            endpoint.path,
            request.user.email,
        )

        return Response(
            {
                "endpoint": endpoint.name,
                "data": payload,
            },
            status=status.HTTP_200_OK,
        )

from django_filters.rest_framework import DjangoFilterBackend

from drf_spectacular.utils import extend_schema

from rest_framework.filters import SearchFilter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsTenantAdmin

from .filters import UsageRecordFilter
from .pagination import UsageCursorPagination
from .serializers import UsageRecordSerializer
from .services import UsageService


@extend_schema(
    summary="Usage dashboard",
    description="List usage records for the current tenant.",
    tags=["Usage"],
)
class UsageListAPIView(ListAPIView):

    serializer_class = UsageRecordSerializer

    permission_classes = [
        IsAuthenticated,
        IsTenantAdmin,
    ]

    pagination_class = UsageCursorPagination

    filter_backends = [
        DjangoFilterBackend,
        SearchFilter,
    ]

    filterset_class = UsageRecordFilter

    search_fields = [
        "user__email",
    ]

    ordering = [
        "-timestamp",
    ]

    def get_queryset(self):
        return UsageService.get_filtered_usage(
            tenant=self.request.user.tenant,
        )