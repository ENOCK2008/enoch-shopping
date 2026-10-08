from rest_framework.permissions import BasePermission, SAFE_METHODS

class CatalogWritePermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and (request.user.is_staff or hasattr(request.user, "seller_profile"))

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_staff or obj.seller.user_id == request.user.id

class CategoryWritePermission(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or (request.user.is_authenticated and request.user.is_staff)
