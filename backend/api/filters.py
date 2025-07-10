from django_filters import rest_framework as filters
from recipes.models import Ingredient, Recipe


class RecipeFilter(filters.FilterSet):
    """
    Фильтры для рецептов:
    - tags: список slug’ов тегов
    - author: id автора
    - is_favorited / is_in_shopping_cart: булевы флаги
    """

    tags = filters.BaseInFilter(field_name="tags__slug", lookup_expr="in")
    author = filters.NumberFilter(field_name="author__id")
    is_favorited = filters.BooleanFilter(method="filter_favorited")
    is_in_shopping_cart = filters.BooleanFilter(
        method="filter_shopping_cart"
    )

    class Meta:
        model = Recipe
        fields = ("tags", "author", "is_favorited", "is_in_shopping_cart")

    def filter_favorited(self, queryset, name, value):
        user = getattr(self.request, "user", None)
        if user is None or user.is_anonymous:
            return queryset.none() if value else queryset

        lookup = {"favorite__user": user}
        qs = (
            queryset.filter(**lookup)
            if value
            else queryset.exclude(**lookup)
        )
        return qs.distinct()

    def filter_shopping_cart(self, queryset, name, value):
        user = getattr(self.request, "user", None)
        if user is None or user.is_anonymous:
            return queryset.none() if value else queryset

        lookup = {"shoppingcart__user": user}
        qs = (
            queryset.filter(**lookup)
            if value
            else queryset.exclude(**lookup)
        )
        return qs.distinct()


class IngredientFilter(filters.FilterSet):
    """Поиск ингредиента по названию, beginnt mit… (istartswith)."""

    name = filters.CharFilter(field_name="name", lookup_expr="istartswith")

    class Meta:
        model = Ingredient
        fields = ("name",)
