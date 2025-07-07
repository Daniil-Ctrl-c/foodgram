import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = "Загружает ингредиенты из файла data/ingredients.json"

    def handle(self, *args, **kwargs):
        data_file = Path(settings.BASE_DIR) / "data" / "ingredients.json"
        if not data_file.exists():
            self.stderr.write(
                self.style.ERROR(f"Файл не найден: {data_file}")
            )
            return

        with data_file.open("r", encoding="utf-8") as f:
            ingredients = json.load(f)

        created_count = 0
        for item in ingredients:
            name = item["name"].strip()
            unit = item["measurement_unit"].strip()
            _, created = Ingredient.objects.get_or_create(
                name=name, measurement_unit=unit
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Успешно загружено {created_count} ингредиентов"
            )
        )
