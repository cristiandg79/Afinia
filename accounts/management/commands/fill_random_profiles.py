import random
from datetime import date
from html import escape
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.choices import HEALTH_CONTEXT_CHOICES
from accounts.models import Profile, ProfilePhoto


class Command(BaseCommand):
    help = 'Rellena todos los usuarios con datos y fotos aleatorias de desarrollo.'

    locations = [
        ('ES', 'Madrid'), ('ES', 'Barcelona'), ('ES', 'Valencia'), ('ES', 'Sevilla'),
        ('ES', 'Zaragoza'), ('ES', 'Málaga'), ('ES', 'Bilbao'), ('ES', 'Alicante'),
        ('MX', 'Ciudad de México'), ('MX', 'Guadalajara'), ('MX', 'Monterrey'),
        ('AR', 'Buenos Aires'), ('AR', 'Córdoba'), ('AR', 'Rosario'),
        ('CO', 'Bogotá'), ('CO', 'Medellín'), ('CO', 'Cali'),
        ('CL', 'Santiago'), ('PE', 'Lima'), ('UY', 'Montevideo'),
    ]
    bios = [
        'Me gusta conocer gente con calma, hablar primero y hacer planes sencillos.',
        'Busco conversaciones honestas, planes tranquilos y personas con empatia.',
        'Me encantan los paseos, el cine, la música y los cafés largos.',
        'Estoy aquí para conocer personas afines sin prisas y con respeto.',
        'Valoro la comunicacion clara, el humor y los espacios accesibles.',
        'Prefiero empezar por chat y quedar cuando ambas personas estemos cómodas.',
        'Me apetecen planes pequeños, gente cercana y conversaciones naturales.',
        'Disfruto de los planes culturales, las tardes tranquilas y aprender cosas nuevas.',
    ]
    interests = ['cafe', 'cinema', 'gaming', 'reading', 'music', 'walks', 'art', 'sports', 'pets', 'support']
    social_preferences = ['chat_first', 'small_groups', 'quiet_places', 'clear_plans', 'slow_pace']
    health_contexts = [[value] for value, _ in HEALTH_CONTEXT_CHOICES] + [
        ['anxiety', 'adhd'],
        ['autism', 'anxiety'],
        ['insomnia', 'anxiety'],
        ['panic_attacks', 'agoraphobia'],
        ['chronic_illness', 'pain_fatigue'],
    ]
    goals = ['dating', 'friendship', 'groups', 'talk']
    palette = [
        ('#256f62', '#f4b69f', '#f7f4ee'),
        ('#8b3f5f', '#f3d6e4', '#fff7fb'),
        ('#2f5f8f', '#d8e8f6', '#f6fbff'),
        ('#8a5a2b', '#f4dfc4', '#fffaf2'),
        ('#3f6f45', '#dcefd9', '#f7fff5'),
        ('#704c86', '#eadcf4', '#fbf7ff'),
        ('#7a4738', '#f2c9b8', '#fff8f4'),
        ('#2f6468', '#cbe8e6', '#f4ffff'),
    ]

    def handle(self, *args, **options):
        users = User.objects.all().order_by('id')
        processed = 0
        photos_created = 0

        for index, user in enumerate(users, start=1):
            profile, _ = Profile.objects.get_or_create(
                user=user,
                defaults={'display_name': user.username},
            )
            sex = random.choice([Profile.Sex.WOMAN, Profile.Sex.MAN, Profile.Sex.NON_BINARY])
            country, city = random.choice(self.locations)
            profile.display_name = user.username
            profile.country = country
            profile.city = city
            profile.province = ''
            profile.bio = random.choice(self.bios)
            profile.goals = self.random_goals()
            profile.interests = random.sample(self.interests, k=random.randint(3, 6))
            profile.social_preferences = random.sample(self.social_preferences, k=random.randint(1, 3))
            profile.health_context = random.choice(self.health_contexts)
            profile.sex = sex
            profile.orientation = random.choices(
                [
                    Profile.Orientation.HETEROSEXUAL,
                    Profile.Orientation.HOMOSEXUAL,
                    Profile.Orientation.BISEXUAL,
                    Profile.Orientation.PANSEXUAL,
                    Profile.Orientation.ASEXUAL,
                ],
                weights=[50, 14, 24, 8, 4],
            )[0]
            profile.birth_date = self.random_birth_date()
            profile.height_cm = random.randint(150, 198)
            profile.weight_kg = random.randint(48, 112)
            profile.smoker = random.choice([
                Profile.Smoker.NO,
                Profile.Smoker.NO,
                Profile.Smoker.SOMETIMES,
                Profile.Smoker.YES,
                Profile.Smoker.PREFER_NOT_SAY,
            ])
            profile.open_to_nearby = True
            profile.open_to_online = random.choice([True, True, False])
            profile.onboarding_completed = True
            profile.save()

            if not profile.photo:
                profile.photo = self.create_svg(profile, index, 'main', profile.user.username[:1].upper())
                profile.save(update_fields=['photo'])
                photos_created += 1

            photos_created += self.ensure_extra_photos(profile, index)
            processed += 1

        self.stdout.write(self.style.SUCCESS(
            f'Perfiles actualizados: {processed}. Fotos demo creadas: {photos_created}.'
        ))

    def random_goals(self):
        selected = random.sample(self.goals, k=random.randint(2, 4))
        if 'dating' not in selected:
            selected[0] = 'dating'
        return selected

    def random_birth_date(self):
        today = date.today()
        age = random.randint(19, 64)
        return date(today.year - age, random.randint(1, 12), random.randint(1, 28))

    def ensure_extra_photos(self, profile, index):
        current_count = profile.extra_photos.count()
        created = 0
        for number in range(current_count + 1, 5):
            image = self.create_svg(profile, index + number, f'extra-{number}', str(number))
            ProfilePhoto.objects.create(profile=profile, image=image)
            created += 1
        return created

    def create_svg(self, profile, seed, kind, label):
        media_dir = Path(settings.MEDIA_ROOT) / 'profiles' / 'demo'
        media_dir.mkdir(parents=True, exist_ok=True)
        bg, fg, soft = self.palette[seed % len(self.palette)]
        escaped_label = escape(label[:2].upper())
        filename = f'{profile.user.username}_{kind}.svg'
        path = media_dir / filename
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="1100" viewBox="0 0 900 1100">'
            f'<rect width="900" height="1100" fill="{soft}"/>'
            f'<circle cx="450" cy="360" r="190" fill="{fg}"/>'
            f'<rect x="150" y="650" width="600" height="360" rx="175" fill="{fg}"/>'
            f'<circle cx="250" cy="220" r="90" fill="{bg}" opacity="0.18"/>'
            f'<circle cx="690" cy="520" r="120" fill="{bg}" opacity="0.14"/>'
            f'<text x="450" y="430" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" '
            f'font-size="190" font-weight="700" fill="{bg}">{escaped_label}</text>'
            '</svg>'
        )
        path.write_text(svg, encoding='utf-8')
        return f'profiles/demo/{filename}'
