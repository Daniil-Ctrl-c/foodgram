import base64

from django.core.files.base import ContentFile
from djoser.views import UserViewSet as BaseUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from users.models import Subscription, User
from users.serializers import SubscriptionSerializer, UserSerializer


class UserViewSet(BaseUserViewSet):
    """
    Расширенный UserViewSet Djoser:
      - подписаться/отписаться
      - список подписок
      - получение/загрузка аватара
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = "id"

    def get_permissions(self):
        if self.action in ["retrieve", "list"]:
            return [AllowAny()]
        return super().get_permissions()

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        author = self.get_object()
        user = request.user

        if author == user:
            return Response(
                {"errors": "Нельзя подписаться на себя"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subscription, created = Subscription.objects.get_or_create(
            user=user, following=author
        )
        if not created:
            return Response(
                {"errors": "Вы уже подписаны"}, status=status.HTTP_400_BAD_REQUEST
            )

        serializer = UserSerializer(author, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        author = self.get_object()
        user = request.user

        try:
            sub = Subscription.objects.get(user=user, following=author)
            sub.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Subscription.DoesNotExist:
            return Response(
                {"errors": "Вы не подписаны"}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
        url_path="subscriptions",
    )
    def subscriptions(self, request):
        user = request.user
        subs_qs = Subscription.objects.filter(user=user)
        page = self.paginate_queryset(subs_qs)
        serializer = SubscriptionSerializer(
            page, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=["get", "patch", "put"],
        permission_classes=[IsAuthenticated],
        url_path="me/avatar",
    )
    def avatar(self, request):
        user = request.user

        if request.method == "GET":
            return Response(
                (
                    {"avatar": request.build_absolute_uri(user.avatar.url)}
                    if user.avatar
                    else {"avatar": None}
                ),
                status=status.HTTP_200_OK,
            )

        file = request.FILES.get("avatar")
        if not file and "avatar" in request.data:
            raw = request.data["avatar"]
            if raw.startswith("data:") and "base64," in raw:
                fmt, imgstr = raw.split("base64,")
                ext = fmt.split("/")[-1].rstrip(";")
                file = ContentFile(base64.b64decode(imgstr), name=f"avatar.{ext}")

        if not file:
            return Response(
                {"errors": "Не передан файл avatar"}, status=status.HTTP_400_BAD_REQUEST
            )

        user.avatar = file
        user.save()
        return Response(
            {"avatar": request.build_absolute_uri(user.avatar.url)},
            status=status.HTTP_200_OK,
        )
