import base64
import uuid

import six
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    """Принимает изображение в формате base64 и сохраняет как ImageField."""

    def to_internal_value(self, data):
        if isinstance(data, six.string_types) and data.startswith(
            "data:image"
        ):
            header, imgstr = data.split(";base64,")
            ext = header.split("/")[-1]
            name = f"{uuid.uuid4().hex[:10]}.{ext}"
            data = ContentFile(base64.b64decode(imgstr), name=name)
        return super().to_internal_value(data)


# ─────────────────────────────── Теги и ингредиенты ────────────────────────────


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "color", "slug")


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class IngredientInRecipeReadSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="ingredient.id")
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit"
    )

    class Meta:
        model = IngredientInRecipe
        fields = ("id", "name", "measurement_unit", "amount")


class IngredientAmountWriteSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source="ingredient", queryset=Ingredient.objects.all()
    )

    class Meta:
        model = IngredientInRecipe
        fields = ("id", "amount")


# ─────────────────────────────── Чтение рецептов ──────────────────────────────


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = serializers.SerializerMethodField()
    # related_name у IngredientInRecipe(recipe) = "ingredient_links"
    ingredients = IngredientInRecipeReadSerializer(
        source="ingredient_links", many=True, read_only=True
    )
    image = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            "id",
            "tags",
            "author",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
            "is_favorited",
            "is_in_shopping_cart",
        )

    def get_author(self, obj):
        from api.users.serializers import UserSerializer

        return UserSerializer(obj.author, context=self.context).data

    def get_image(self, obj):
        request = self.context.get("request")
        return (
            request.build_absolute_uri(obj.image.url)
            if obj.image and request
            else None
        )

    def get_is_favorited(self, obj):
        user = self.context.get("request").user
        # related_name у Recipe->Favorite = "favorite"
        return (
            False
            if user.is_anonymous
            else obj.favorite.filter(user=user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get("request").user
        return (
            False
            if user.is_anonymous
            else obj.shoppingcart.filter(user=user).exists()
        )


# ─────────────────────────────── Запись рецептов ──────────────────────────────


class RecipeWriteSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountWriteSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = (
            "tags",
            "ingredients",
            "name",
            "image",
            "text",
            "cooking_time",
        )

    def _save_tags_and_ingredients(self, recipe, tags, ingredients):
        recipe.tags.set(tags)
        # related_name у IngredientInRecipe(recipe) = "ingredient_links"
        recipe.ingredient_links.all().delete()
        IngredientInRecipe.objects.bulk_create(
            [
                IngredientInRecipe(
                    recipe=recipe,
                    ingredient=item["ingredient"],
                    amount=item["amount"],
                )
                for item in ingredients
            ]
        )

    def create(self, validated_data):
        tags = validated_data.pop("tags")
        ingredients = validated_data.pop("ingredients")
        recipe = Recipe.objects.create(
            author=self.context["request"].user, **validated_data
        )
        self._save_tags_and_ingredients(recipe, tags, ingredients)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        ingredients = validated_data.pop("ingredients", None)
        instance = super().update(instance, validated_data)
        self._save_tags_and_ingredients(
            instance,
            tags or instance.tags.all(),
            ingredients or [],
        )
        return instance


# ─────────────────────────────── Универсальный фасад ──────────────────────────


class RecipeSerializer(serializers.Serializer):
    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data

    def to_internal_value(self, data):
        return RecipeWriteSerializer(
            data=data, context=self.context
        ).run_validation(data)

    def create(self, validated_data):
        return RecipeWriteSerializer(context=self.context).create(
            validated_data
        )

    def update(self, instance, validated_data):
        return RecipeWriteSerializer(context=self.context).update(
            instance, validated_data
        )


# ──────────────────────── Сериализаторы для связей «рецепт‒юзер» ──────────────


class _RelationBaseSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(write_only=True)

    class Meta:
        fields = ("id",)
        extra_kwargs = {"id": {"write_only": True}}

    def validate(self, attrs):
        recipe_id = attrs["id"]
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        attrs["recipe"] = recipe
        user = self.context["request"].user
        attrs["user"] = user
        model = self.Meta.model
        if model.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError("Уже добавлено")
        return attrs


class FavoriteCreateSerializer(_RelationBaseSerializer):
    class Meta(_RelationBaseSerializer.Meta):
        model = Favorite


class ShoppingCartCreateSerializer(_RelationBaseSerializer):
    class Meta(_RelationBaseSerializer.Meta):
        model = ShoppingCart
