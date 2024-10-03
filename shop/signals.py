from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile, UserRegistrationStatistic, Order, Review, Notification

@receiver(post_save, sender=User)
def user_profile_and_statistic(sender, instance, created, **kwargs):
    """Create a UserRegistrationStatistic and Profile when a new user is created."""
    if created:
        # Create UserRegistrationStatistic
        UserRegistrationStatistic.objects.create(user=instance)
        
        # Create Profile
        Profile.objects.create(user=instance)
    else:
        # Save the Profile when the User is updated
        instance.profile.save()

@receiver(post_save, sender=Order)
def create_order_notification(sender, instance, created, **kwargs):
    """Create a notification when an order is placed."""
    if created:
        Notification.objects.create(user=instance.user, message='Your order has been placed successfully!')

@receiver(post_save, sender=Review)
def create_review_notification(sender, instance, created, **kwargs):
    """Create a notification when a review is submitted."""
    if created:
        Notification.objects.create(user=instance.product.owner, message=f'{instance.user.username} reviewed your product: {instance.comment}')
