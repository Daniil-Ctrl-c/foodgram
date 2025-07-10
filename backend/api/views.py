from django.db.models import Count, F, Sum
from django.http import HttpResponse

from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as BaseUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from api.serializers import (
    AvatarSerializer,
    FavoriteCreateSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeSerializer,
    ShoppingCartCreateSerializer,
    SubscriptionCreateSerializer,
    SubscriptionSerializer,
    TagSerializer,
    UserCreateSerializer,
    UserSerializer,
)
from recipes.filters import IngredientFilter, RecipeFilter
from recipes.models import Ingredient, IngredientInRecipe, Recipe, Tag
from users.models import Subscription, User

# ─────────────────────────────── Пользователи ───────────────────────────


class UserViewSet(BaseUserViewSet):
    """Пользователи + подписки + аватар."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    create_serializer_class = UserCreateSerializer
    lookup_field = "id"

    def get_permissions(self):
        if self.action in ["retrieve", "list", "me"]:
            return [AllowAny()]
        return super().get_permissions()

    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        if request.user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = UserSerializer(
            request.user, context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True, methods=["post"], permission_classes=[IsAuthenticated],
    )
    def subscribe(self, request, id=None):
        serializer = SubscriptionCreateSerializer(
            data={"following": id}, context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        subscription = serializer.save()
        output = SubscriptionSerializer(
            subscription, context={"request": request},
        )
        return Response(output.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        deleted, _ = Subscription.objects.filter(
            user=request.user, following_id=id,
        ).delete()
        if not deleted:
            return Response(
                {"errors": "Вы не подписаны"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="subscriptions",
    )
    def subscriptions(self, request):
        qs = (
            Subscription.objects.filter(user=request.user)
            .select_related("following")
            .annotate(recipes_count=Count("following__recipes"))
        )
        page = self.paginate_queryset(qs)
        serializer = SubscriptionSerializer(
            page, many=True, context={"request": request},
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=["get", "patch", "put"],
        permission_classes=[IsAuthenticated],
        url_path="me/avatar",
    )
    def avatar(self, request):
        if request.method == "GET":
            serializer = AvatarSerializer(
                request.user, context={"request": request},
            )
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = AvatarSerializer(
            request.user,
            data=request.data,
            context={"request": request},
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


# ─────────────────────────────── Теги и ингредиенты ─────────────────────


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


# ─────────────────────────────── Рецепты ────────────────────────────────


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related("author").prefetch_related(
        "tags", "ingredient_links__ingredient",
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

    def _modify_relation(self, serializer_cls, request, pk, add=True):
        if add:
            serializer = serializer_cls(
                data={"id": pk}, context={"request": request},
            )
            serializer.is_valid(raise_exception=True)
            relation = serializer.save()
            data = RecipeReadSerializer(
                relation.recipe, context={"request": request},
            ).data
            return Response(data, status=status.HTTP_201_CREATED)

        model = serializer_cls.Meta.model
        deleted, _ = model.objects.filter(
            user=request.user, recipe_id=pk,
        ).delete()
        if not deleted:
            return Response(
                {"errors": "Не найдено"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"])
    def favorite(self, request, pk=None):
        return self._modify_relation(
            FavoriteCreateSerializer, request, pk, add=True,
        )

    @favorite.mapping.delete
    def delete_favorite(self, request, pk=None):
        return self._modify_relation(
            FavoriteCreateSerializer, request, pk, add=False,
        )

    @action(detail=True, methods=["post"])
    def shopping_cart(self, request, pk=None):
        return self._modify_relation(
            ShoppingCartCreateSerializer, request, pk, add=True,
        )

    @shopping_cart.mapping.delete
    def delete_shopping_cart(self, request, pk=None):
        return self._modify_relation(
            ShoppingCartCreateSerializer, request, pk, add=False,
        )

    @action(detail=False, methods=["get"], url_path="shopping_cart")
    def shopping_cart_list(self, request):
        qs = Recipe.objects.filter(shoppingcart__user=request.user)
        page = self.paginate_queryset(qs)
        data = RecipeReadSerializer(
            page, many=True, context={"request": request},
        ).data
        return self.get_paginated_response(data)

    @action(detail=False, methods=["get"], url_path="favorite")
    def favorite_list(self, request):
        qs = Recipe.objects.filter(favorite__user=request.user)
        page = self.paginate_queryset(qs)
        data = RecipeReadSerializer(
            page, many=True, context={"request": request},
        ).data
        return self.get_paginated_response(data)

    def _build_shopping_list_text(self, request):
        items = (
            IngredientInRecipe.objects.filter(
                recipe__shoppingcart__user=request.user,
            )
            .values(
                name=F("ingredient__name"),
                unit=F("ingredient__measurement_unit"),
            )
            .annotate(total=Sum("amount"))
        )
        return "\n".join(
            f"{item['name']} — {item['total']} {item['unit']}"
            for item in items
        )

    @action(
        detail=False, methods=["get"], url_path="download_shopping_cart",
    )
    def download_shopping_cart(self, request):
        content = self._build_shopping_list_text(request)
        response = HttpResponse(content, content_type="text/plain")
        response["Content-Disposition"] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response
