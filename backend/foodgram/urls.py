from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import TemplateView

urlpatterns = [
    # Grappelli (тема админки)
    path("grappelli/", include("grappelli.urls")),
    # Стандартная админка
    path("admin/", admin.site.urls),
    # API рецептов (рецепты, теги, ингредиенты)
    path("api/", include("recipes.urls")),
    # API пользователей и подписок (перенесено в новое API-приложение)
    path("api/users/", include("api.users.urls")),
    # Djoser аутентификация
    path("api/auth/", include("djoser.urls")),
    path("api/auth/", include("djoser.urls.authtoken")),
]

# Статика и медиа в режиме отладки
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )

# Всё остальное — отдаём React-приложение
urlpatterns += [
    re_path(
        r"^(?!api/|static/|media/).*$",
        TemplateView.as_view(template_name="index.html"),
    ),
]
