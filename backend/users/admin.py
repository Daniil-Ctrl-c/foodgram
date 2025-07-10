from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from recipes.models import ShoppingCart
from users.models import Subscription

User = get_user_model()


class ShoppingCartInline(admin.TabularInline):
    model = ShoppingCart
    extra = 0
    autocomplete_fields = ("recipe",)
    verbose_name = "Рецепт в корзине"
    verbose_name_plural = "Корзина (Inline)"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Дополнительно", {"fields": ("avatar",)}),
    )
    readonly_fields = ("avatar",)
    inlines = (ShoppingCartInline,)

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "is_active",
        "is_staff",
        "avatar",
    )
    list_display_links = ("username", "email")
    list_filter = ("is_staff", "is_active")
    # добавлен поиск по ФИО
    search_fields = ("username", "email", "first_name", "last_name")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "following")
    list_filter = ("user", "following")
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "following__username",
        "following__first_name",
        "following__last_name",
    )
    autocomplete_fields = ("user", "following")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("user", "following")
        )
