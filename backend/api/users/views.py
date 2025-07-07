from api.users.serializers import (
    AvatarSerializer,
    SubscriptionCreateSerializer,
    SubscriptionSerializer,
    UserCreateSerializer,
    UserSerializer,
)
from django.db.models import Count
from djoser.views import UserViewSet as BaseUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import Subscription, User


class UserViewSet(BaseUserViewSet):
    """Пользователи + подписки + аватар."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    create_serializer_class = UserCreateSerializer
    lookup_field = "id"

    # — permissions —
    def get_permissions(self):
        if self.action in ["retrieve", "list", "me"]:
            return [AllowAny()]
        return super().get_permissions()

    # — текущий пользователь —
    @action(detail=False, methods=["get"], url_path="me")
    def me(self, request):
        if request.user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = UserSerializer(
            request.user, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    # ──────────────── подписка / отписка ──────────────────────────────────────
    @action(
        detail=True, methods=["post"], permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        serializer = SubscriptionCreateSerializer(
            data={"following": id}, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        subscription = serializer.save()

        output = SubscriptionSerializer(
            subscription,
            context={"request": request},
        )
        return Response(output.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        deleted, _ = Subscription.objects.filter(
            user=request.user, following_id=id
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
            page, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    # ────────────────────────────────── аватар ───────────────────────────────
    @action(
        detail=False,
        methods=["get", "patch", "put"],
        permission_classes=[IsAuthenticated],
        url_path="me/avatar",
    )
    def avatar(self, request):
        if request.method == "GET":
            serializer = AvatarSerializer(
                request.user, context={"request": request}
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
