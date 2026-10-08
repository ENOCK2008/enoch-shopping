from django.conf import settings
from django.db import models


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('system', 'System'),
        ('shipment', 'Shipment'),
        ('order', 'Order'),
        ('message', 'Message'),
        ('account', 'Account'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=180)
    message = models.TextField()
    kind = models.CharField(max_length=50, default='system')
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES, default='system')
    related_id = models.IntegerField(null=True, blank=True)
    related_type = models.CharField(max_length=50, blank=True)
    is_read = models.BooleanField(default=False)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_read']),
        ]

    def __str__(self):
        return f"{self.title} - {self.user.username}"
