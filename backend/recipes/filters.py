from django_filters import rest_framework as filters
from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(filters.FilterSet):
    # IN-фильтр по slug-ам тегов
    tags = filters.BaseInFilter(
        field_name="tags__slug",
        lookup_expr="in"
    )
    author = filters.NumberFilter(field_name="author__id")
    is_favorited = filters.BooleanFilter(method="filter_favorited")
    is_in_shopping_cart = filters.BooleanFilter(method="filter_shopping_cart")

    class Meta:
        model = Recipe
        fields = (
            "tags",             # теперь принимает список ?tags=egg,milk,...
            "author",
            "is_favorited",
            "is_in_shopping_cart",
        )

    def filter_favorited(self, queryset, name, value):
        user = getattr(self.request, "user", None)
        if not user or user.is_anonymous:
            return queryset.none() if value else queryset
        qs = (
            queryset.filter(favorited_by__user=user)
            if value
            else queryset.exclude(favorited_by__user=user)
        )
        return qs.distinct()

    def filter_shopping_cart(self, queryset, name, value):
        user = getattr(self.request, "user", None)
        if not user or user.is_anonymous:
            return queryset.none() if value else queryset
        qs = (
            queryset.filter(shopping_carts__user=user)
            if value
            else queryset.exclude(shopping_carts__user=user)
        )
        return qs.distinct()


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(
        field_name="name",
        lookup_expr="istartswith"
    )

    class Meta:
        model = Ingredient
        fields = ("name",)
