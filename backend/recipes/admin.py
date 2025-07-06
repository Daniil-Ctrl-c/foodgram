from django.contrib import admin
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
        "id",
        "name",
        "author",
        "cooking_time",
        "favorite_count",
        "image_thumbnail",
    )
    list_filter = (
        "tags",
        "author",
        # "cooking_time",  # оставим обычный числовой фильтр, без range
    )
    search_fields = ("name", "author__username")
    autocomplete_fields = ("tags",)
    filter_horizontal = ("tags",)
    readonly_fields = ("image_thumbnail",)
    actions = ("export_to_csv",)

    class Media:
        js = ("admin/js/positive_only.js",)

    def image_thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:60px;border-radius:4px;" />',
                obj.image.url,
            )
        return "-"

    image_thumbnail.short_description = "Фото"

    def favorite_count(self, obj):
        return obj.favorited_by.count()

    favorite_count.short_description = "В избранном"

    def export_to_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse

        field_names = ["id", "name", "author", "cooking_time"]
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=recipes.csv"
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow(
                [obj.id, obj.name, obj.author.username, obj.cooking_time]
            )
        return response

    export_to_csv.short_description = "Экспорт выбранных рецептов в CSV"


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


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ("user", "recipe")
    list_filter = ("user",)
    autocomplete_fields = ("user", "recipe")
