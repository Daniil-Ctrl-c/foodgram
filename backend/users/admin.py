from django.contrib import admin
from django.utils.html import format_html
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from users.models import Subscription
from recipes.models import ShoppingCart

User = get_user_model()


class ShoppingCartInline(admin.TabularInline):
    model = ShoppingCart
    extra = 0
    autocomplete_fields = ('recipe',)
    verbose_name = 'Рецепт в корзине'
    verbose_name_plural = 'Корзина (Inline)'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительно', {'fields': ('avatar', 'avatar_thumbnail')}),
    )
    readonly_fields = ('avatar_thumbnail',)
    inlines = (ShoppingCartInline,)

    list_display = (
        'id', 'username', 'email',
        'is_active', 'is_staff',
        'avatar_thumbnail', 'subscriptions_count'
    )
    list_filter = ('is_staff', 'is_active')
    search_fields = ('username', 'email')

    def avatar_thumbnail(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" style="width:40px;border-radius:20px;" />',
                obj.avatar.url
            )
        return "-"
    avatar_thumbnail.short_description = 'Аватар'

    def subscriptions_count(self, obj):
        # Считаем, сколько пользователей подписано на данного пользователя
        return Subscription.objects.filter(following=obj).count()
    subscriptions_count.short_description = 'Подписчиков'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'following')
    search_fields = ('user__username', 'following__username')
    autocomplete_fields = ('user', 'following')
