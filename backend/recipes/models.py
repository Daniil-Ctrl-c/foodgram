from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name="Название тега")
    color = models.CharField(max_length=7, verbose_name="Цвет (HEX)")
    slug = models.SlugField(unique=True, verbose_name="Слаг")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"


class Ingredient(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name="Название ингредиента")
    measurement_unit = models.CharField(max_length=200, verbose_name="Единица измерения")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Ингредиент"
        verbose_name_plural = "Ингредиенты"


class Recipe(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipes",
        verbose_name="Автор"
    )
    name = models.CharField(max_length=200, verbose_name="Название")
    image = models.ImageField(upload_to="recipes/images/", verbose_name="Изображение")
    text = models.TextField(verbose_name="Описание")
    cooking_time = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(1440)],
        verbose_name="Время приготовления (мин)"
    )
    # Восстанавливаем through-модель, чтобы не ломать миграции
    tags = models.ManyToManyField(
        Tag,
        through="RecipeTag",
        related_name="recipes",
        verbose_name="Теги"
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through="IngredientInRecipe",
        related_name="recipes",
        verbose_name="Ингредиенты"
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Рецепт"
        verbose_name_plural = "Рецепты"


class RecipeTag(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("recipe", "tag")
        verbose_name = "Тег рецепта"
        verbose_name_plural = "Теги рецептов"

    def __str__(self):
        return f"{self.recipe} — {self.tag}"


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="ingredientinrecipe_set",
        verbose_name="Рецепт"
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name="ingredientinrecipe_set",
        verbose_name="Ингредиент"
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Количество"
    )

    def __str__(self):
        return f"{self.ingredient} в {self.recipe}: {self.amount}"

    class Meta:
        verbose_name = "Ингредиент в рецепте"
        verbose_name_plural = "Ингредиенты в рецептах"
        unique_together = ("recipe", "ingredient")


class RecipeRelation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE, verbose_name="Рецепт")

    class Meta:
        abstract = True
        unique_together = ("user", "recipe")


class Favorite(RecipeRelation):
    def __str__(self):
        return f"{self.user} добавил {self.recipe} в избранное"

    class Meta:
        verbose_name = "Избранное"
        verbose_name_plural = "Избранные рецепты"


class ShoppingCart(RecipeRelation):
    def __str__(self):
        return f"{self.user} добавил {self.recipe} в корзину"

    class Meta:
        db_table = "recipes_cart"
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"
