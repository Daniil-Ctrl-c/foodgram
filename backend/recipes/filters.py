from django_filters import rest_framework as filters
from recipes.models import Ingredient, Recipe, Tag


class RecipeFilter(filters.FilterSet):
    # заменили AllValuesMultipleFilter на методовый фильтр
    tags = filters.CharFilter(method="filter_tags")
    author = filters.NumberFilter(field_name="author__id")
    is_favorited = filters.BooleanFilter(method="filter_favorited")
    is_in_shopping_cart = filters.BooleanFilter(method="filter_shopping_cart")

    class Meta:
        model = Recipe
        fields = ("tags", "author", "is_favorited", "is_in_shopping_cart")

    def filter_tags(self, queryset, name, value):
        # собираем все переданные ?tags=...
        slugs = self.request.query_params.getlist("tags")
        # оставляем только существующие слаги
        valid = Tag.objects.filter(slug__in=slugs).values_list(
            "slug", flat=True
        )
        if not valid:
            return queryset  # если ни один слаг не валиден — не фильтруем
        return queryset.filter(tags__slug__in=valid).distinct()

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
    # фильтрация autocomplete по началу имени
    name = filters.CharFilter(field_name="name", lookup_expr="istartswith")

    class Meta:
        model = Ingredient
        fields = ("name",)
