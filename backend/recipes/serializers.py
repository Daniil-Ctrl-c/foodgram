import base64
import uuid

import six
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from recipes.models import Ingredient, IngredientInRecipe, Recipe, Tag
from rest_framework import serializers

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, six.string_types) and data.startswith(
            "data:image"
        ):
            header, imgstr = data.split(";base64,")
            ext = header.split("/")[-1]
            name = f"{uuid.uuid4().hex[:10]}.{ext}"
            data = ContentFile(base64.b64decode(imgstr), name=name)
        return super().to_internal_value(data)


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


class IngredientAmountWriteSerializer(serializers.Serializer):
    """
    Принимает два формата:
      - {"id": <pk>, "amount": <n>}
      - {"ingredient": {"id": <pk>}, "amount": <n>}
    """

    id = serializers.IntegerField(required=False)
    ingredient = serializers.DictField(
        child=serializers.IntegerField(), required=False
    )
    amount = serializers.IntegerField(min_value=1)

    def validate(self, data):
        pk = data.get("id") or data.get("ingredient", {}).get("id")
        if not pk:
            raise serializers.ValidationError("Нужен id ингредиента.")
        return data


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = serializers.SerializerMethodField()
    ingredients = IngredientInRecipeReadSerializer(
        source="ingredientinrecipe_set", many=True, read_only=True
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
        from users.serializers import UserSerializer

        return UserSerializer(obj.author, context=self.context).data

    def get_image(self, obj):
        req = self.context.get("request")
        return (
            req.build_absolute_uri(obj.image.url)
            if obj.image and req
            else None
        )

    def get_is_favorited(self, obj):
        req = self.context.get("request")
        return bool(
            req
            and not req.user.is_anonymous
            and obj.favorited_by.filter(user=req.user).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        req = self.context.get("request")
        return bool(
            req
            and not req.user.is_anonymous
            and obj.shopping_carts.filter(user=req.user).exists()
        )


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

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError("Нужен хотя бы один ингредиент.")
        seen = set()
        for item in value:
            pk = item.get("id") or item.get("ingredient", {}).get("id")
            if pk in seen:
                raise serializers.ValidationError(
                    "Ингредиенты не должны повторяться."
                )
            seen.add(pk)
        return value

    def create(self, validated_data):
        tags = validated_data.pop("tags")
        ingr_data = validated_data.pop("ingredients")
        user = self.context["request"].user
        recipe = Recipe.objects.create(author=user, **validated_data)
        recipe.tags.set(tags)

        bulk = []
        for item in ingr_data:
            pk = item.get("id") or item.get("ingredient", {}).get("id")
            ingr = Ingredient.objects.get(pk=pk)
            bulk.append(
                IngredientInRecipe(
                    recipe=recipe, ingredient=ingr, amount=item["amount"]
                )
            )
        IngredientInRecipe.objects.bulk_create(bulk)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop("tags", None)
        ingr_data = validated_data.pop("ingredients", None)

        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        if tags is not None:
            instance.tags.set(tags)
        if ingr_data is not None:
            instance.ingredientinrecipe_set.all().delete()
            bulk = []
            for item in ingr_data:
                pk = item.get("id") or item.get("ingredient", {}).get("id")
                ingr = Ingredient.objects.get(pk=pk)
                bulk.append(
                    IngredientInRecipe(
                        recipe=instance, ingredient=ingr, amount=item["amount"]
                    )
                )
            IngredientInRecipe.objects.bulk_create(bulk)
        instance.save()
        return instance


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
