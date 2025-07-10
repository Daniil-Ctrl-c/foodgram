import csv
from django.contrib import admin
from django.db.models import Count
from django.http import HttpResponse
from django.utils.html import format_html

from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag,
)


class IngredientInRecipeInline(admin.TabularInline):
    model = IngredientInRecipe
    extra = 1
    autocomplete_fields = ("ingredient",)
    min_num = 1


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Основное", {"fields": ("name", "author", "text")}),
        ("Теги и время", {"fields": ("cooking_time",)}),
        ("Изображение", {"fields": ("image", "image_thumbnail")}),
    )
    inlines = (IngredientInRecipeInline,)

    list_display = (
        "name",
        "author",
        "cooking_time",
        "favorite_count",
        "image_thumbnail",
        "id",
    )
    list_display_links = ("name",)
    list_filter = ("tags", "author")
    search_fields = ("name", "author__username")
    autocomplete_fields = ("tags",)
    filter_horizontal = ("tags",)
    readonly_fields = ("image_thumbnail",)
    actions = ("export_to_csv",)

    class Media:
        js = ("admin/js/positive_only.js",)

    def get_queryset(self, request):
        qs = (
            super()
            .get_queryset(request)
            .select_related("author")
            .prefetch_related("tags", "ingredientinrecipe_set__ingredient")
            .annotate(favorite_count=Count("favorite"))
        )
        return qs

    @admin.display(description="Фото")
    def image_thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:60px;border-radius:4px;" />',
                obj.image.url,
            )
        return "-"

    @admin.display(description="В избранном", ordering="favorite_count")
    def favorite_count(self, obj):
        return obj.favorite_count

    @admin.action(description="Экспорт выбранных рецептов в CSV")
    def export_to_csv(self, request, queryset):
        field_names = ["id", "name", "author", "cooking_time"]
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=recipes.csv"
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow(
                [obj.id, obj.name, obj.author.username, obj.cooking_time],
            )
        return response


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "measurement_unit")
    search_fields = ("^name",)
    list_filter = ("measurement_unit",)
    ordering = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "color")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("color",)
    search_fields = ("name",)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    list_filter = ("user",)

    def get_queryset(self, request):
        return (
            super().get_queryset(request).select_related("user", "recipe")
        )


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    list_filter = ("user",)
    search_fields = ("user__username", "recipe__name")

    def get_queryset(self, request):
        return (
            super().get_queryset(request).select_related("user", "recipe")
        )
