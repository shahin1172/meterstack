from rest_framework import serializers
from tenants.models import Tenant
from tenants.services import create_tenant_with_admin   # <-- the service

class TenantRegistrationSerializer(serializers.ModelSerializer):
    admin_username = serializers.CharField(write_only=True)
    admin_email = serializers.EmailField(write_only=True)
    admin_password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Tenant
        fields = ['name', 'slug', 'admin_username', 'admin_email', 'admin_password']
        extra_kwargs = {'slug': {'required': False}}

    def create(self, validated_data: dict) -> Tenant:
        # The serializer only passes data to the service – no heavy logic here
        tenant, admin = create_tenant_with_admin(
            tenant_name=validated_data['name'],
            tenant_slug=validated_data.get('slug'),
            admin_username=validated_data['admin_username'],
            admin_email=validated_data['admin_email'],
            admin_password=validated_data['admin_password'],
        )
        return tenant


#alternative version without service
#from rest_framework import serializers
#from django.utils.text import slugify
#from tenants.models import Tenant
#from users.models import User


#class TenantRegistrationSerializer(serializers.ModelSerializer):
#    # Admin user fields – these are not part of the Tenant model
#    admin_username = serializers.CharField(max_length=150, write_only=True)
#    admin_email = serializers.EmailField(write_only=True)
#    admin_password = serializers.CharField(write_only=True, min_length=8)

#    class Meta:
#        model = Tenant
#        fields = ['name', 'slug', 'admin_username', 'admin_email', 'admin_password']
#        extra_kwargs = {
#            'slug': {'required': False},   # slug is optional; we'll generate it if not given
#        }

#    def create(self, validated_data: dict) -> Tenant:
#        # 1. Take the admin user fields out of the basket (pop)
#        admin_username = validated_data.pop('admin_username')
#        admin_email = validated_data.pop('admin_email')
#        admin_password = validated_data.pop('admin_password')

#        # 2. If slug is missing or empty, generate one from the tenant name
#        if not validated_data.get('slug'):
#            validated_data['slug'] = slugify(validated_data['name'])

#        # 3. Create the Tenant – now validated_data only contains name and slug
#        tenant = Tenant.objects.create(**validated_data)

#        # 4. Create the admin User (password is securely hashed by create_user)
#        User.objects.create_user(
#            username=admin_username,
#            email=admin_email,
#            password=admin_password,
#            tenant=tenant,
#            role=User.Role.ADMIN,       # or just 'admin' depending on your model's choices
#        )

#        # 5. Return the newly created tenant (the view will return it in the response)
#        return tenant

