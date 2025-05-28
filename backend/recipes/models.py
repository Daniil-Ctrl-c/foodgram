from django.db import models
from users.models import User  # или ваш путь к модели User


class Tag(models.Model):
    name = models.CharField(max_length=200, unique=True)
    color = models.CharField(max_length=7)
    slug = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(max_length=200, unique=True)
    measurement_unit = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recipes"
    )
    name = models.CharField(max_length=200)
    image = models.ImageField(upload_to="recipes/images/")
    text = models.TextField()
    cooking_time = models.PositiveIntegerField()
    tags = models.ManyToManyField(
        Tag, through="RecipeTag", related_name="recipes"
    )
    ingredients = models.ManyToManyField(
        Ingredient, through="IngredientInRecipe", related_name="recipes"
    )

    def __str__(self):
        return self.name


class RecipeTag(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("recipe", "tag")


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="ingredientinrecipe_set"
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="ingredientinrecipe_set",
    )
    amount = models.PositiveIntegerField()

    class Meta:
        unique_together = ("recipe", "ingredient")


class Favorite(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="favorites"
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="favorited_by"
    )

    class Meta:
        unique_together = ("user", "recipe")


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="cart_items"
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name="shopping_carts"
    )

    class Meta:
        # Использовать существующую таблицу recipes_cart
        db_table = "recipes_cart"
        unique_together = ("user", "recipe")
