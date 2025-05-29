from django.db.models import F, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from recipes.filters import IngredientFilter, RecipeFilter
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)
from recipes.serializers import (
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeSerializer,
    TagSerializer,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related("author").prefetch_related(
        "tags", "ingredientinrecipe_set__ingredient"
    )
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_permissions(self):
        if self.action in (
            "create",
            "partial_update",
            "destroy",
            "favorite",
            "delete_favorite",
            "shopping_cart",
            "delete_shopping_cart",
            "shopping_cart_list",
            "favorite_list",
            "download_shopping_cart",
        ):
            return [IsAuthenticated()]
        return super().get_permissions()

    def _modify_relation(self, model, request, pk, add=True):
        recipe = get_object_or_404(Recipe, pk=pk)
        lookup = {"user": request.user, "recipe": recipe}
        qs = model.objects.filter(**lookup)
        if add:
            if qs.exists():
                return Response(
                    {"errors": "Уже добавлено"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            model.objects.create(**lookup)
            data = RecipeReadSerializer(
                recipe, context={"request": request}
            ).data
            return Response(data, status=status.HTTP_201_CREATED)
        deleted, _ = qs.delete()
        if not deleted:
            return Response(
                {"errors": "Не найдено"}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def favorite(self, request, pk=None):
        return self._modify_relation(Favorite, request, pk, add=True)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        return self._modify_relation(Favorite, request, pk, add=False)

    @action(detail=True, methods=["post"])
    def shopping_cart(self, request, pk=None):
        return self._modify_relation(ShoppingCart, request, pk, add=True)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        return self._modify_relation(ShoppingCart, request, pk, add=False)

    @action(detail=False, methods=["get"], url_path="shopping_cart")
    def shopping_cart_list(self, request):
        qs = Recipe.objects.filter(shopping_carts__user=request.user)
        page = self.paginate_queryset(qs)
        data = RecipeReadSerializer(
            page, many=True, context={"request": request}
        ).data
        return self.get_paginated_response(data)

    @action(detail=False, methods=["get"], url_path="favorite")
    def favorite_list(self, request):
        qs = Recipe.objects.filter(favorited_by__user=request.user)
        page = self.paginate_queryset(qs)
        data = RecipeReadSerializer(
            page, many=True, context={"request": request}
        ).data
        return self.get_paginated_response(data)

    @action(detail=False, methods=["get"], url_path="download_shopping_cart")
    def download_shopping_cart(self, request):
        qs = (
            IngredientInRecipe.objects.filter(
                recipe__shopping_carts__user=request.user
            )
            .values(
                name=F("ingredient__name"),
                unit=F("ingredient__measurement_unit"),
            )
            .annotate(total=Sum("amount"))
        )
        lines = [
            f"{item['name']} — {item['total']} {item['unit']}" for item in qs
        ]
        content = "\n".join(lines)
        resp = HttpResponse(content, content_type="text/plain")
        resp["Content-Disposition"] = (
            'attachment; filename="shopping_list.txt"'
        )
        return resp
