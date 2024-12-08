from django.utils import timezone
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from account.models import Profile  # Замените 'your_app' на фактическое имя вашего приложения

class Command(BaseCommand):
    help = 'Удаляет просроченные группы пользователей'

    def handle(self, *args, **options):
        users = User.objects.all()
        for user in users:
            profile = Profile.objects.get(user=user)
            if profile.group_expiration_date and profile.group_expiration_date < timezone.now():
                remove_all_groups(user)  # Удаляем все группы
                profile.group_activation_date = None
                profile.group_expiration_date = None
                profile.save()
                self.stdout.write(f'Группа удалена для пользователя {user.username}')