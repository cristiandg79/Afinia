import random
from datetime import date
from html import escape
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import Profile


class Command(BaseCommand):
    help = 'Crea perfiles demo con datos de citas y fotos principales.'

    first_names = [
        'Alex', 'Clara', 'Dani', 'Marta', 'Sergio', 'Nerea', 'Iker', 'Laura',
        'Hugo', 'Paula', 'Mario', 'Sara', 'Adrian', 'Noa', 'Javi', 'Elena',
        'Leo', 'Aitana', 'Ruben', 'Irene', 'Samuel', 'Eva', 'Bruno', 'Luna',
    ]
    cities = [
        ('Madrid', 'Madrid'), ('Barcelona', 'Barcelona'), ('Valencia', 'Valencia'),
        ('Sevilla', 'Sevilla'), ('Zaragoza', 'Zaragoza'), ('Malaga', 'Malaga'),
        ('Bilbao', 'Bizkaia'), ('Alicante', 'Alicante'), ('Vigo', 'Pontevedra'),
        ('Granada', 'Granada'), ('Murcia', 'Murcia'), ('Valladolid', 'Valladolid'),
    ]
    interests = ['cafe', 'cinema', 'gaming', 'reading', 'music', 'walks', 'art', 'sports', 'support']
    social_preferences = ['chat_first', 'small_groups', 'quiet_places', 'clear_plans', 'slow_pace']
    health_contexts = [
        ['anxiety'], ['depression'], ['autism'], ['adhd'], ['physical_disability'],
        ['chronic_illness'], ['hearing_disability'], ['pain_fatigue'], ['prefer_not_detail'],
    ]
    bios = [
        'Me gusta conocer gente con calma, hablar primero y hacer planes sencillos.',
        'Busco una conexión honesta, sin prisas y con buena conversación.',
        'Me encantan los paseos tranquilos, el cine y los cafés largos.',
        'Estoy aquí para conocer personas afines y construir algo bonito poco a poco.',
        'Valoro la empatia, el humor y los planes accesibles.',
        'Prefiero empezar por chat y quedar cuando ambas personas estemos cómodas.',
    ]

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=72)

    def handle(self, *args, **options):
        count = options['count']
        created = 0
        for index in range(count):
            first_name = random.choice(self.first_names)
            username = f'demo_{first_name.lower()}_{index + 1:03d}'
            email = f'{username}@example.com'
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={'email': email, 'first_name': first_name},
            )
            if user_created:
                user.set_password('demo12345')
                user.save()
                created += 1

            sex = random.choice([Profile.Sex.WOMAN, Profile.Sex.MAN])
            orientation = random.choices(
                [
                    Profile.Orientation.HETEROSEXUAL,
                    Profile.Orientation.HOMOSEXUAL,
                    Profile.Orientation.BISEXUAL,
                    Profile.Orientation.PANSEXUAL,
                ],
                weights=[55, 15, 22, 8],
            )[0]
            city, province = random.choice(self.cities)
            profile, _ = Profile.objects.update_or_create(
                user=user,
                defaults={
                    'display_name': username,
                    'city': city,
                    'province': province,
                    'bio': random.choice(self.bios),
                    'goals': random.sample(['dating', 'friendship', 'talk', 'groups'], k=random.randint(1, 3)),
                    'interests': random.sample(self.interests, k=random.randint(3, 6)),
                    'social_preferences': random.sample(self.social_preferences, k=random.randint(1, 3)),
                    'health_context': random.choice(self.health_contexts),
                    'sex': sex,
                    'orientation': orientation,
                    'birth_date': self.random_birth_date(),
                    'height_cm': random.randint(150, 196),
                    'weight_kg': random.randint(48, 105),
                    'smoker': random.choice([Profile.Smoker.NO, Profile.Smoker.NO, Profile.Smoker.SOMETIMES, Profile.Smoker.YES]),
                    'open_to_nearby': True,
                    'open_to_online': random.choice([True, True, False]),
                    'onboarding_completed': True,
                },
            )
            if 'dating' not in profile.goals:
                profile.goals = ['dating'] + list(profile.goals)
                profile.save(update_fields=['goals'])
            self.ensure_avatar(profile, first_name, sex, index)

        self.stdout.write(self.style.SUCCESS(f'Perfiles demo listos. Usuarios nuevos: {created}. Total procesado: {count}.'))

    def random_birth_date(self):
        today = date.today()
        age = random.randint(19, 62)
        year = today.year - age
        return date(year, random.randint(1, 12), random.randint(1, 28))

    def ensure_avatar(self, profile, first_name, sex, index):
        if profile.photo:
            return
        avatar_dir = Path(settings.MEDIA_ROOT) / 'profiles' / 'demo'
        avatar_dir.mkdir(parents=True, exist_ok=True)
        colors = [
            ('#256f62', '#f4b69f'), ('#8b3f5f', '#f3d6e4'), ('#2f5f8f', '#d8e8f6'),
            ('#8a5a2b', '#f4dfc4'), ('#3f6f45', '#dcefd9'), ('#704c86', '#eadcf4'),
        ]
        bg, fg = colors[index % len(colors)]
        initial = escape(first_name[:1].upper())
        filename = f'{profile.user.username}.svg'
        path = avatar_dir / filename
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="1100" viewBox="0 0 900 1100">'
            f'<rect width="900" height="1100" fill="{bg}"/>'
            f'<circle cx="450" cy="390" r="180" fill="{fg}" opacity="0.92"/>'
            f'<rect x="150" y="650" width="600" height="360" rx="170" fill="{fg}" opacity="0.92"/>'
            f'<text x="450" y="445" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" '
            f'font-size="210" font-weight="700" fill="{bg}">{initial}</text>'
            '</svg>'
        )
        path.write_text(svg, encoding='utf-8')
        profile.photo = f'profiles/demo/{filename}'
        profile.save(update_fields=['photo'])
