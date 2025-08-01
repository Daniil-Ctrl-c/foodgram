from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Tag(models.Model):
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="Название тега",
    )
    color = models.CharField(max_length=7, verbose_name="Цвет (HEX)")
    slug = models.SlugField(unique=True, verbose_name="Слаг")

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        max_length=200,
        unique=True,
        verbose_name="Название ингредиента",
    )
    measurement_unit = models.CharField(
        max_length=200,
        verbose_name="Единица измерения",
    )

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор",
    )
    name = models.CharField(max_length=200, verbose_name="Название")
    image = models.ImageField(
        upload_to="recipes/images/",
        verbose_name="Изображение",
    )
    text = models.TextField(verbose_name="Описание")
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(1440),
        ],
        verbose_name="Время приготовления (мин)",
    )
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )
    tags = models.ManyToManyField(
        Tag,
        related_name="recipes",
        verbose_name="Теги",
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through="IngredientInRecipe",
        related_name="recipes",
        verbose_name="Ингредиенты",
    )

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"
        ordering = ["-created"]

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="ingredient_links",
        verbose_name="Рецепт",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="recipe_links",
        verbose_name="Ингредиент",
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10000),
        ],
        verbose_name="Количество",
    )

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"
        unique_together = ("recipe", "ingredient")

    def __str__(self):
        return f"{self.ingredient} – {self.amount} (в {self.recipe})"


class RecipeRelation(models.Model):
    """Абстрактная связь «пользователь — рецепт» (избранное, корзина)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="%(class)s",
        verbose_name="Пользователь",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="%(class)s",
        verbose_name="Рецепт",
    )

    class Meta:
        abstract = True
        unique_together = ("user", "recipe")


class Favorite(RecipeRelation):
    class Meta(RecipeRelation.Meta):
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные рецепты"

    def __str__(self):
        return f"{self.user} → избранное → {self.recipe}"


class ShoppingCart(RecipeRelation):
    class Meta(RecipeRelation.Meta):
        db_table = "recipes_cart"
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"

    def __str__(self):
        return f"{self.user} → корзина → {self.recipe}"
