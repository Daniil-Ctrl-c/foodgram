from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    avatar = models.ImageField(
        upload_to="users/avatars/", null=True, blank=True
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    def __str__(self):
        return self.email


class Subscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="subscriptions",
        on_delete=models.CASCADE,
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="subscribers",
        on_delete=models.CASCADE,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "following"], name="unique_subscription"
            )
        ]

    def __str__(self):
        return f"{self.user.email} follows {self.following.email}"
