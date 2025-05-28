import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Загружает ингредиенты из файла data/ingredients.json"

    def handle(self, *args, **kwargs):
        path = os.path.join(settings.BASE_DIR, "data", "ingredients.json")

        if not os.path.exists(path):
            self.stderr.write(self.style.ERROR(f"Файл не найден: {path}"))
            return

        with open(path, "r", encoding="utf-8") as file:
            ingredients = json.load(file)

        count = 0
        for item in ingredients:
            name = item["name"].strip()
            unit = item["measurement_unit"].strip()
            _, created = Ingredient.objects.get_or_create(
                name=name, measurement_unit=unit
            )
            if created:
                count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Успешно загружено {count} ингредиентов")
        )
