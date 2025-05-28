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
    queryset = Recipe.objects.all()
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

    @action(detail=True, methods=["post"])
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if recipe.favorited_by.filter(user=request.user).exists():
            return Response(
                {"errors": "Уже в избранном"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        Favorite.objects.create(user=request.user, recipe=recipe)
        data = RecipeReadSerializer(recipe, context={"request": request}).data
        return Response(data, status=status.HTTP_201_CREATED)

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        fav = recipe.favorited_by.filter(user=request.user)
        if not fav.exists():
            return Response(
                {"errors": "Не в избранном"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        fav.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        if recipe.shopping_carts.filter(user=request.user).exists():
            return Response(
                {"errors": "Уже в корзине"}, status=status.HTTP_400_BAD_REQUEST
            )
        ShoppingCart.objects.create(user=request.user, recipe=recipe)
        data = RecipeReadSerializer(recipe, context={"request": request}).data
        return Response(data, status=status.HTTP_201_CREATED)

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        item = recipe.shopping_carts.filter(user=request.user)
        if not item.exists():
            return Response(
                {"errors": "Не в корзине"}, status=status.HTTP_400_BAD_REQUEST
            )
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

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
        qs = IngredientInRecipe.objects.filter(
            recipe__shopping_carts__user=request.user
        )
        if not qs.exists():
            return Response(
                {"errors": "Корзина пуста"}, status=status.HTTP_400_BAD_REQUEST
            )
        ingredients = {}
        for item in qs:
            name = item.ingredient.name
            unit = item.ingredient.measurement_unit
            ingredients[(name, unit)] = (
                ingredients.get((name, unit), 0) + item.amount
            )
        content = ""
        for (name, unit), amount in ingredients.items():
            content += f"{name} — {amount} {unit}\n"
        resp = HttpResponse(content, content_type="text/plain")
        resp["Content-Disposition"] = (
            'attachment; filename="shopping_list.txt"'
        )
        return resp

    @action(detail=True, methods=["get"], url_path="get_link")
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        url = request.build_absolute_uri(f"/recipes/{recipe.pk}/")
        return Response({"link": url})
