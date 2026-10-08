from rest_framework import serializers
from .models import SellerProfile

class SellerProfileSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username", read_only=True)
    class Meta:
        model = SellerProfile
        fields = "__all__"
        read_only_fields = ["user", "verified", "created_at"]
