from api.recipes.serializers import (
    FavoriteCreateSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeSerializer,
    ShoppingCartCreateSerializer,
    TagSerializer,
)
from django.db.models import F, Sum
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from recipes.filters import IngredientFilter, RecipeFilter
from recipes.models import Ingredient, IngredientInRecipe, Recipe, Tag
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
        "tags", "ingredient_links__ingredient"
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

    # ─────────────────────── избранное / корзина ────────────────────────────
    def _modify_relation(self, serializer_cls, request, pk, add=True):
        if add:
            serializer = serializer_cls(
                data={"id": pk}, context={"request": request}
            )
            serializer.is_valid(raise_exception=True)
            relation = serializer.save()
            data = RecipeReadSerializer(
                relation.recipe, context={"request": request}
            ).data
            return Response(data, status=status.HTTP_201_CREATED)

        # удаление
        model = serializer_cls.Meta.model
        deleted, _ = model.objects.filter(
            user=request.user, recipe_id=pk
        ).delete()
        if not deleted:
            return Response(
                {"errors": "Не найдено"}, status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def favorite(self, request, pk=None):
        return self._modify_relation(
            FavoriteCreateSerializer, request, pk, add=True
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        return self._modify_relation(
            FavoriteCreateSerializer, request, pk, add=False
        )

    @action(detail=True, methods=["post"])
    def shopping_cart(self, request, pk=None):
        return self._modify_relation(
            ShoppingCartCreateSerializer, request, pk, add=True
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        return self._modify_relation(
            ShoppingCartCreateSerializer, request, pk, add=False
        )

    # ─────────────────────────── списки избранное / корзина ──────────────────
    @action(detail=False, methods=["get"], url_path="shopping_cart")
    def shopping_cart_list(self, request):
        qs = Recipe.objects.filter(shoppingcart__user=request.user)
        page = self.paginate_queryset(qs)
        data = RecipeReadSerializer(
            page, many=True, context={"request": request}
        ).data
        return self.get_paginated_response(data)

    @action(detail=False, methods=["get"], url_path="favorite")
    def favorite_list(self, request):
        qs = Recipe.objects.filter(favorite__user=request.user)
        page = self.paginate_queryset(qs)
        data = RecipeReadSerializer(
            page, many=True, context={"request": request}
        ).data
        return self.get_paginated_response(data)

    # ─────────────────────────── download_shopping_cart ──────────────────────
    def _build_shopping_list(self, request):
        """Формирует txt-файл со списком покупок."""
        items = (
            IngredientInRecipe.objects.filter(
                recipe__shoppingcart__user=request.user
            )
            .values(
                name=F("ingredient__name"),
                unit=F("ingredient__measurement_unit"),
            )
            .annotate(total=Sum("amount"))
        )
        lines = [
            f"{item['name']} — {item['total']} {item['unit']}"
            for item in items
        ]
        content = "\n".join(lines)
        response = HttpResponse(content, content_type="text/plain")
        response["Content-Disposition"] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(
        detail=False, methods=["get"], url_path="download_shopping_cart"
    )
    def download_shopping_cart(self, request):
        return self._build_shopping_list(request)
