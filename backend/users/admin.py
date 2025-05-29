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
    fieldsets = BaseUserAdmin.fieldsets + \
        (("Дополнительно", {"fields": ("avatar",)}),)
    readonly_fields = ("avatar",)
    inlines = (ShoppingCartInline,)
    list_display = ("username", "email", "is_active", "is_staff", "avatar")
    list_display_links = ("username", "email")
    list_filter = ("is_staff", "is_active")
    search_fields = ("username", "email")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "following")
    list_filter = ("user", "following")
    search_fields = ("user__username", "following__username")
    autocomplete_fields = ("user", "following")
