from base64 import b64decode
from django.core.files.base import ContentFile
from djoser.views import UserViewSet as BaseUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import Subscription, User
from api.users.serializers import (
    SubscriptionSerializer, UserCreateSerializer, UserSerializer
)


class UserViewSet(BaseUserViewSet):
    """Профиль пользователя и подписки."""
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
        """Текущий пользователь."""
        if request.user.is_anonymous:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        """Оформить подписку."""
        serializer = SubscriptionSerializer(
            data={"following": id},
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(
            UserSerializer(self.get_object(), context={"request": request}).data,
            status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        """Отменить подписку."""
        deleted, _ = Subscription.objects.filter(
            user=request.user, following_id=id
        ).delete()
        if not deleted:
            return Response(
                {"errors": "Вы не подписаны"},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated], url_path="subscriptions")
    def subscriptions(self, request):
        """Список моих подписок."""
        qs = Subscription.objects.filter(user=request.user).select_related("following")
        page = self.paginate_queryset(qs)
        serializer = SubscriptionSerializer(page, many=True, context={"request": request})
        return self.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get", "patch", "put"], permission_classes=[IsAuthenticated], url_path="me/avatar")
    def avatar(self, request):
        """Получить/обновить аватар."""
        if request.method == "GET":
            avatar = (
                request.build_absolute_uri(request.user.avatar.url)
                if request.user.avatar else None
            )
            return Response({"avatar": avatar}, status=status.HTTP_200_OK)

        raw = request.data.get("avatar")
        if raw and raw.startswith("data:") and "base64," in raw:
            fmt, imgstr = raw.split("base64,")
            ext = fmt.split("/")[-1].rstrip(";")
            file = ContentFile(b64decode(imgstr), name=f"avatar.{ext}")
            request.user.avatar = file
            request.user.save()
            return Response(
                {"avatar": request.build_absolute_uri(request.user.avatar.url)},
                status=status.HTTP_200_OK
            )

        return Response(
            {"errors": "Не передан файл avatar"},
            status=status.HTTP_400_BAD_REQUEST
        )
