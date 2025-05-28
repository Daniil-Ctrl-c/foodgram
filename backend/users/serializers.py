
from django.contrib.auth import get_user_model
from djoser.serializers import \
    UserCreateSerializer as DjoserUserCreateSerializer
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from recipes.serializers import Base64ImageField, RecipeReadSerializer
from users.models import Subscription

User = get_user_model()


class UserCreateSerializer(DjoserUserCreateSerializer):
    """
    Сериализатор для регистрации нового пользователя с поддержкой avatar.
    """

    avatar = Base64ImageField(max_length=None, use_url=True, required=False)

    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = tuple(DjoserUserCreateSerializer.Meta.fields) + ("avatar",)


class UserSerializer(DjoserUserSerializer):
    """
    Расширяем стандартный сериализатор Djoser:
      - возможность загрузки avatar (base64)
      - поле is_subscribed
    """

    avatar = Base64ImageField(max_length=None, use_url=True, required=False)
    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        model = User
        fields = tuple(DjoserUserSerializer.Meta.fields) + (
            "avatar",
            "is_subscribed",
        )

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        if not request or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(user=request.user, following=obj).exists()


class SubscriptionSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="following.id")
    email = serializers.EmailField(source="following.email", read_only=True)
    username = serializers.ReadOnlyField(source="following.username")
    first_name = serializers.ReadOnlyField(source="following.first_name")
    last_name = serializers.ReadOnlyField(source="following.last_name")
    avatar = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def get_avatar(self, obj):
        request = self.context.get("request")
        avatar = obj.following.avatar
        return request.build_absolute_uri(avatar.url) if avatar and request else None

    def get_is_subscribed(self, obj):
        return True

    def get_recipes(self, obj):
        qs = obj.following.recipes.all()[:3]
        return RecipeReadSerializer(qs, many=True, context=self.context).data

    def get_recipes_count(self, obj):
        return obj.following.recipes.count()
