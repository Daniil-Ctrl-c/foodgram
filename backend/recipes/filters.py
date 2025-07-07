from django_filters import rest_framework as filters
from recipes.models import Ingredient, Recipe


class RecipeFilter(filters.FilterSet):
    tags = filters.BaseInFilter(field_name="tags__slug", lookup_expr="in")
    author = filters.NumberFilter(field_name="author__id")
    is_favorited = filters.BooleanFilter(method="filter_favorited")
    is_in_shopping_cart = filters.BooleanFilter(
        method="filter_shopping_cart"
    )

    class Meta:
        model = Recipe
        fields = ("tags", "author", "is_favorited", "is_in_shopping_cart")

    # --- избранное --------------------------------------------------------
    def filter_favorited(self, queryset, name, value):
        """
        true  -> вернуть рецепты, которые пользователь добавил в избранное
        false -> исключить такие рецепты
        """
        user = getattr(self.request, "user", None)
        if user is None or user.is_anonymous:
            # гость → избранных/корзины быть не может
            return queryset.none() if value else queryset

        lookup = {"favorite__user": user}
        return (
            queryset.filter(**lookup)
            if value
            else queryset.exclude(**lookup)
        ).distinct()

    # --- корзина ----------------------------------------------------------
    def filter_shopping_cart(self, queryset, name, value):
        """
        true  -> рецепты, находящиеся в корзине пользователя
        false -> рецепты, не находящиеся в корзине
        """
        user = getattr(self.request, "user", None)
        if user is None or user.is_anonymous:
            return queryset.none() if value else queryset

        lookup = {"shoppingcart__user": user}
        return (
            queryset.filter(**lookup)
            if value
            else queryset.exclude(**lookup)
        ).distinct()


class IngredientFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr="istartswith")

    class Meta:
        model = Ingredient
        fields = ("name",)
