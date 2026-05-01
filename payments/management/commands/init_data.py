from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from payments.models import Item


class Command(BaseCommand):
    help = 'Создаёт тестовые данные для Stripe демо'

    def handle(self, *args, **options):
        
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

        users_data = [
            {
                'username': 'admin',
                'email': 'admin@example.com',
                'password': 'admin123',
                'is_staff': True,
                'is_superuser': True,
            },
            {
                'username': 'testuser',
                'email': 'testuser@example.com',
                'password': 'test123',
                'is_staff': False,
                'is_superuser': False,
            },
        ]

        for user_data in users_data:
            username = user_data['username']
            password = user_data.pop('password')
            user, created = User.objects.get_or_create(
                username=username,
                defaults={k: v for k, v in user_data.items() if k != 'username'}
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Создан пользователь: {username}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Пользователь уже существует: {username}')
                )
