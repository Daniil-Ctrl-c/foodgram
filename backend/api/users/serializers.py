from api.recipes.serializers import Base64ImageField
from djoser.serializers import (
    UserCreateSerializer as BaseUserCreateSerializer,
)
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers
from users.models import Subscription, User


# ────────────────────────────── Пользователь ──────────────────────────────────
class UserCreateSerializer(BaseUserCreateSerializer):
    """Регистрация пользователя (с аватаром, опционально)."""

    avatar = Base64ImageField(max_length=None, use_url=True, required=False)

    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = (*BaseUserCreateSerializer.Meta.fields, "avatar")


class UserSerializer(BaseUserSerializer):
    """Профиль пользователя + флаг подписки."""

    avatar = Base64ImageField(max_length=None, use_url=True, required=False)
    is_subscribed = serializers.SerializerMethodField()

    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = (
            *BaseUserSerializer.Meta.fields,
            "avatar",
            "is_subscribed",
        )

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        return (
            False
            if not request or request.user.is_anonymous
            else Subscription.objects.filter(
                user=request.user, following=obj
            ).exists()
        )


# ──────────────────────── Подписки (создание / вывод) ─────────────────────────
class SubscriptionCreateSerializer(serializers.ModelSerializer):
    """Создание подписки через POST /users/{id}/subscribe/."""

    following = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True
    )

    class Meta:
        model = Subscription
        fields = ("following",)

    def validate(self, attrs):
        user = self.context["request"].user
        following = attrs["following"]
        if user == following:
            raise serializers.ValidationError("Нельзя подписаться на себя")
        if Subscription.objects.filter(
            user=user, following=following
        ).exists():
            raise serializers.ValidationError("Уже подписаны")
        attrs["user"] = user
        return attrs


class SubscriptionSerializer(serializers.ModelSerializer):
    """Данные о подписке (read-only)."""

    id = serializers.ReadOnlyField(source="following.id")
    email = serializers.ReadOnlyField(source="following.email")
    username = serializers.ReadOnlyField(source="following.username")
    first_name = serializers.ReadOnlyField(source="following.first_name")
    last_name = serializers.ReadOnlyField(source="following.last_name")
    avatar = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(read_only=True)

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

    # — helpers —
    def get_avatar(self, obj):
        request = self.context.get("request")
        avatar = obj.following.avatar
        return (
            request.build_absolute_uri(avatar.url)
            if avatar and request
            else None
        )

    def get_is_subscribed(self, obj):
        return True  # мы отдаем только мои подписки

    def get_recipes(self, obj):
        from api.recipes.serializers import RecipeReadSerializer

        qs = obj.following.recipes.all()[:3]
        return RecipeReadSerializer(
            qs, many=True, context=self.context
        ).data


# ──────────────────────────── Аватар ──────────────────────────────────────────
class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True, use_url=True)

    class Meta:
        model = User
        fields = ("avatar",)

    def to_representation(self, instance):
        request = self.context.get("request")
        avatar = instance.avatar
        return {
            "avatar": (
                request.build_absolute_uri(avatar.url)
                if avatar and request
                else None
            )
        }
