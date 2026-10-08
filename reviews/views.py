from rest_framework import permissions, viewsets
from .models import Review
from .serializers import ReviewSerializer

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    queryset = Review.objects.select_related("user", "product").order_by("-created_at")
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
