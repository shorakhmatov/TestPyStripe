from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Загружает тестовые данные из фикстуры'

    def handle(self, *args, **options):
        self.stdout.write('Загрузка данных...')
        call_command('loaddata', 'initial_data')
        self.stdout.write(self.style.SUCCESS('Готово!'))
