"""
Команда для создания тестовых данных.

TODO: Реализуй создание тестовых Item после того как создашь модель.
"""

from django.core.management.base import BaseCommand
from payments.models import Item


class Command(BaseCommand):
    help = 'Создаёт тестовые товары для Stripe демо'

    def handle(self, *args, **options):
        # TODO: После создания модели Item, раскомментируй:
        
        items_data = [
            {
                'name': 'iPhone 15 Pro',
                'description': 'Смартфон Apple с титановым корпусом',
                'price': 99900,  # $999.00
                'currency': 'usd',
            },
            {
                'name': 'MacBook Air M3',
                'description': 'Ультратонкий ноутбук с чипом M3',
                'price': 129900,  # $1299.00
                'currency': 'usd',
            },
            {
                'name': 'AirPods Pro 2',
                'description': 'Беспроводные наушники с шумоподавлением',
                'price': 24900,  # $249.00
                'currency': 'usd',
            },
            {
                'name': 'iPad Pro 12.9"',
                'description': 'Планшет с дисплеем Liquid Retina XDR',
                'price': 109900,  # $1099.00
                'currency': 'eur',  # Бонус: товар в евро
            },
        ]
        
        for item_data in items_data:
            item, created = Item.objects.get_or_create(
                name=item_data['name'],
                defaults=item_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Создан товар: {item.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Товар уже существует: {item.name}')
                )
        
        self.stdout.write(self.style.SUCCESS('Готово!'))
