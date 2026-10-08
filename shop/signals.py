from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile, UserRegistrationStatistic, Order, Review, Notification

@receiver(post_save, sender=User)
def user_profile_and_statistic(sender, instance, created, **kwargs):
    """
    Create a UserRegistrationStatistic and Profile when a new user is created,
    and save the Profile when the user is updated.
    """
    if created:
        try:
            # Create UserRegistrationStatistic
            UserRegistrationStatistic.objects.create(user=instance)
            
            # Create Profile
            Profile.objects.create(user=instance)
        except Exception as e:
            # Log or handle the error as appropriate
            print(f"Error creating user profile or statistic: {e}")
    else:
        # Save the Profile when the User is updated
        if hasattr(instance, 'profile'):  # Ensure the user has a profile
            try:
                instance.profile.save()
            except Exception as e:
                # Log or handle the error as appropriate
                print(f"Error saving profile for user {instance.username}: {e}")

@receiver(post_save, sender=Order)
def create_order_notification(sender, instance, created, **kwargs):
    """
    Create a notification when an order is placed.
    """
    if created:
        try:
            # Create a notification for the user
            Notification.objects.create(user=instance.user, message='Your order has been placed successfully!')
        except Exception as e:
            # Log or handle the error as appropriate
            print(f"Error creating notification for order {instance.id}: {e}")

@receiver(post_save, sender=Review)
def create_review_notification(sender, instance, created, **kwargs):
    """
    Create a notification when a review is submitted.
    """
    if created:
        try:
            # Notify the product owner of the new review
            Notification.objects.create(
                user=instance.product.owner,
                message=f'{instance.user.username} reviewed your product: {instance.comment}'
            )
        except Exception as e:
            # Log or handle the error as appropriate
            print(f"Error creating notification for review of product {instance.product.id}: {e}")
