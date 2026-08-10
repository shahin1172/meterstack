from rest_framework import serializers
from tenants.models import Tenant
from tenants.services import create_tenant_with_admin


class TenantRegistrationSerializer(serializers.ModelSerializer):
    admin_username = serializers.CharField(write_only=True)
    admin_email = serializers.EmailField(write_only=True)
    admin_password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Tenant
        fields = ['name', 'slug', 'admin_username', 'admin_email', 'admin_password']
        extra_kwargs = {'slug': {'required': False}}

    def create(self, validated_data: dict) -> Tenant:
        tenant, admin = create_tenant_with_admin(
            tenant_name=validated_data['name'],
            tenant_slug=validated_data.get('slug'),
            admin_username=validated_data['admin_username'],
            admin_email=validated_data['admin_email'],
            admin_password=validated_data['admin_password'],
        )
        return tenant