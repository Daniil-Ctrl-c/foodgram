from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer
from recipes.serializers import Base64ImageField, RecipeReadSerializer
from rest_framework import serializers
from users.models import Subscription, User


class UserCreateSerializer(BaseUserCreateSerializer):
    """Регистрация пользователя с аватаром."""

    avatar = Base64ImageField(max_length=None, use_url=True, required=False)

    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = (*BaseUserCreateSerializer.Meta.fields, "avatar")


class UserSerializer(BaseUserSerializer):
    """Профиль пользователя с аватаром и флагом подписки."""

    avatar = Base64ImageField(max_length=None, use_url=True, required=False)
    is_subscribed = serializers.SerializerMethodField()

    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = (*BaseUserSerializer.Meta.fields, "avatar", "is_subscribed")

    def get_is_subscribed(self, obj):
        request = self.context.get("request")
        return bool(
            request
            and not request.user.is_anonymous
            and Subscription.objects.filter(user=request.user, following=obj).exists()
        )


class SubscriptionSerializer(serializers.ModelSerializer):
    """Информация о подписке."""

    id = serializers.ReadOnlyField(source="following.id")
    email = serializers.EmailField(source="following.email", read_only=True)
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

    def get_avatar(self, obj):
        request = self.context.get("request")
        avatar = obj.following.avatar
        return request.build_absolute_uri(avatar.url) if avatar and request else None

    def get_is_subscribed(self, obj):
        return True

    def get_recipes(self, obj):
        qs = obj.following.recipes.all()[:3]
        return RecipeReadSerializer(qs, many=True, context=self.context).data
