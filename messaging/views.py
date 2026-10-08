from rest_framework import permissions, viewsets
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Conversation.objects.filter(buyer=self.request.user).prefetch_related("messages")
    def perform_create(self, serializer):
        serializer.save(buyer=self.request.user)

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Message.objects.filter(conversation__buyer=self.request.user)
    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)
