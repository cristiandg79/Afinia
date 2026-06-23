import random
import shutil
import unicodedata
from datetime import date
from pathlib import Path

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.models import Q

from PIL import Image, ImageDraw, ImageFilter

from accounts.choices import HEALTH_CONTEXT_CHOICES
from accounts.models import Profile, ProfilePhoto


class Command(BaseCommand):
    help = 'Crea perfiles demo con datos de citas y una foto principal generada.'

    first_names = [
        'Lucia', 'Clara', 'Marta', 'Nerea', 'Laura', 'Paula', 'Sara', 'Elena',
        'Irene', 'Aitana', 'Eva', 'Luna', 'Nadia', 'Vera', 'Carmen', 'Ines',
        'Carlos', 'Dani', 'Sergio', 'Iker', 'Hugo', 'Mario', 'Adrian', 'Javi',
        'Leo', 'Ruben', 'Samuel', 'Bruno', 'Pablo', 'Diego', 'Marcos', 'Mateo',
    ]
    last_names = [
        'Soler', 'Marin', 'Vidal', 'Ramos', 'Castro', 'Molina', 'Navas', 'Ruiz',
        'Iglesias', 'Campos', 'Santos', 'Herrera', 'Leon', 'Cortes', 'Pardo',
        'Rey', 'Lozano', 'Fuentes', 'Bravo', 'Sanz', 'Gil', 'Ortega', 'Prieto',
        'Vega',
    ]
    cities = [
        ('Madrid', 'Madrid'), ('Barcelona', 'Barcelona'), ('Valencia', 'Valencia'),
        ('Sevilla', 'Sevilla'), ('Zaragoza', 'Zaragoza'), ('Malaga', 'Malaga'),
        ('Bilbao', 'Bizkaia'), ('Alicante', 'Alicante'), ('Vigo', 'Pontevedra'),
        ('Granada', 'Granada'), ('Murcia', 'Murcia'), ('Valladolid', 'Valladolid'),
        ('Badalona', 'Barcelona'), ('Hospitalet de Llobregat', 'Barcelona'),
        ('Cornella de Llobregat', 'Barcelona'), ('Sabadell', 'Barcelona'),
    ]
    interests = ['cafe', 'cinema', 'gaming', 'reading', 'music', 'walks', 'art', 'sports', 'support', 'pets']
    social_preferences = ['chat_first', 'small_groups', 'quiet_places', 'clear_plans', 'slow_pace']
    bios = [
        'Me gusta conocer gente con calma, hablar primero y hacer planes sencillos.',
        'Busco una conexion honesta, sin prisas y con buena conversacion.',
        'Me encantan los paseos tranquilos, el cine y los cafes largos.',
        'Estoy aqui para conocer personas afines y construir algo bonito poco a poco.',
        'Valoro la empatia, el humor y los planes accesibles.',
        'Prefiero empezar por chat y quedar cuando ambas personas estemos comodas.',
        'Me apetecen planes pequenos, gente cercana y conversaciones naturales.',
        'Disfruto de la musica, los planes culturales y las tardes tranquilas.',
    ]
    skin_tones = ['#f1c9a5', '#d9a06f', '#b8794d', '#8f5d3d', '#f5d6bc', '#c9875d']
    hair_colors = ['#2c1d17', '#4b2f21', '#6b3d25', '#a45d2b', '#1f2933', '#7a5c45']
    shirt_colors = ['#256f62', '#2f5f8f', '#8b3f5f', '#7a4738', '#3f6f45', '#704c86', '#c25d3f']
    background_colors = ['#dbeee8', '#f4dfd1', '#dbe7f4', '#eee4f5', '#f3ecd9', '#e5f0dc']

    def add_arguments(self, parser):
        parser.add_argument('--count', type=int, default=72)
        parser.add_argument('--reset', action='store_true', help='Borra demos y tests anteriores antes de crear.')

    def handle(self, *args, **options):
        count = options['count']
        if options['reset']:
            self.delete_demo_users()

        random.seed(20260623)
        created = 0
        for index in range(count):
            first_name = self.first_names[index % len(self.first_names)]
            last_name = self.last_names[(index * 5) % len(self.last_names)]
            username = self.unique_username(first_name, last_name, index + 1)
            email = f'{username}@demo.afinia.local'
            user, user_created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': username,
                    'first_name': first_name,
                    'last_name': last_name,
                },
            )
            if user_created:
                user.set_password('demo12345')
                user.save()
                created += 1

            sex = self.pick_sex(first_name)
            orientation = random.choices(
                [
                    Profile.Orientation.HETEROSEXUAL,
                    Profile.Orientation.HOMOSEXUAL,
                    Profile.Orientation.BISEXUAL,
                    Profile.Orientation.PANSEXUAL,
                    Profile.Orientation.ASEXUAL,
                ],
                weights=[50, 14, 24, 8, 4],
            )[0]
            city, province = random.choice(self.cities)
            profile, _ = Profile.objects.update_or_create(
                user=user,
                defaults={
                    'display_name': f'{first_name} {last_name}',
                    'country': 'ES',
                    'city': city,
                    'province': province,
                    'bio': random.choice(self.bios),
                    'goals': self.random_goals(),
                    'interests': random.sample(self.interests, k=random.randint(3, 6)),
                    'social_preferences': random.sample(self.social_preferences, k=random.randint(1, 3)),
                    'health_context': self.random_health_context(),
                    'sex': sex,
                    'orientation': orientation,
                    'birth_date': self.random_birth_date(),
                    'height_cm': random.randint(150, 196),
                    'weight_kg': random.randint(48, 105),
                    'smoker': random.choice([Profile.Smoker.NO, Profile.Smoker.NO, Profile.Smoker.SOMETIMES]),
                    'open_to_nearby': True,
                    'open_to_online': random.choice([True, True, False]),
                    'onboarding_completed': True,
                },
            )
            self.replace_photo(profile, first_name, last_name, sex, index)

        self.stdout.write(self.style.SUCCESS(
            f'Perfiles demo recreados: {count}. Usuarios nuevos: {created}.'
        ))

    def delete_demo_users(self):
        User.objects.filter(
            Q(username__startswith='demo_')
            | Q(username__startswith='test_')
            | Q(email__endswith='@demo.afinia.local')
            | Q(email__endswith='@test.afinia.local')
        ).delete()
        demo_dir = Path(settings.MEDIA_ROOT) / 'profiles' / 'demo'
        if demo_dir.exists() and demo_dir.resolve().is_relative_to(Path(settings.MEDIA_ROOT).resolve()):
            shutil.rmtree(demo_dir)

    def unique_username(self, first_name, last_name, number):
        base = f'{self.slug(first_name)}_{self.slug(last_name)}'
        username = f'{base}_{number:02d}'
        suffix = number
        while User.objects.filter(username=username).exists():
            suffix += 1
            username = f'{base}_{suffix:02d}'
        return username

    def slug(self, value):
        normalized = unicodedata.normalize('NFKD', value)
        ascii_value = ''.join(char for char in normalized if not unicodedata.combining(char))
        return ''.join(char.lower() for char in ascii_value if char.isalnum())

    def pick_sex(self, first_name):
        female_names = {
            'Lucia', 'Clara', 'Marta', 'Nerea', 'Laura', 'Paula', 'Sara', 'Elena',
            'Irene', 'Aitana', 'Eva', 'Luna', 'Nadia', 'Vera', 'Carmen', 'Ines',
        }
        return Profile.Sex.WOMAN if first_name in female_names else Profile.Sex.MAN

    def random_goals(self):
        selected = random.sample(['dating', 'friendship', 'talk', 'groups'], k=random.randint(2, 4))
        if 'dating' not in selected:
            selected[0] = 'dating'
        return selected

    def random_health_context(self):
        values = [value for value, _ in HEALTH_CONTEXT_CHOICES]
        return random.sample(values, k=random.randint(1, min(2, len(values))))

    def random_birth_date(self):
        today = date.today()
        age = random.randint(22, 58)
        return date(today.year - age, random.randint(1, 12), random.randint(1, 28))

    def replace_photo(self, profile, first_name, last_name, sex, index):
        if profile.photo:
            profile.photo.delete(save=False)
        for photo in list(profile.extra_photos.all()):
            photo.image.delete(save=False)
            photo.delete()

        ai_portrait = self.ai_portrait_for(index)
        if ai_portrait:
            profile.photo = f'profiles/demo_ai/{ai_portrait.name}'
        else:
            main_path = self.create_portrait(profile.user.username, first_name, last_name, sex, index, 'main')
            profile.photo = f'profiles/demo/{main_path.name}'
        profile.save(update_fields=['photo'])

    def ai_portrait_for(self, index):
        ai_dir = Path(settings.MEDIA_ROOT) / 'profiles' / 'demo_ai'
        portraits = sorted(ai_dir.glob('ai_portrait_*.png'))
        if not portraits:
            return None
        return portraits[index % len(portraits)]

    def create_portrait(self, username, first_name, last_name, sex, seed, kind):
        rng = random.Random(seed)
        media_dir = Path(settings.MEDIA_ROOT) / 'profiles' / 'demo'
        media_dir.mkdir(parents=True, exist_ok=True)
        path = media_dir / f'{username}_{kind}.png'

        image = Image.new('RGB', (900, 1100), rng.choice(self.background_colors))
        draw = ImageDraw.Draw(image)
        self.draw_background(draw, rng)

        skin = rng.choice(self.skin_tones)
        hair = rng.choice(self.hair_colors)
        shirt = rng.choice(self.shirt_colors)
        face_box = (290, 230, 610, 590)
        neck_box = (390, 555, 510, 735)
        body_box = (185, 680, 715, 1160)

        shadow = Image.new('RGBA', image.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.ellipse((260, 240, 640, 620), fill=(0, 0, 0, 36))
        shadow_draw.rounded_rectangle((160, 700, 740, 1120), radius=230, fill=(0, 0, 0, 28))
        shadow = shadow.filter(ImageFilter.GaussianBlur(26))
        image = Image.alpha_composite(image.convert('RGBA'), shadow)
        draw = ImageDraw.Draw(image)

        draw.rounded_rectangle(body_box, radius=240, fill=shirt)
        draw.rectangle(neck_box, fill=skin)
        self.draw_hair(draw, rng, hair, sex)
        draw.ellipse(face_box, fill=skin)
        self.draw_face(draw, rng)
        self.draw_clothes(draw, rng, shirt)
        self.draw_photo_texture(image, rng)

        image = image.convert('RGB')
        image.save(path, quality=92)
        return path

    def draw_background(self, draw, rng):
        for _ in range(9):
            x = rng.randint(-100, 850)
            y = rng.randint(-100, 1000)
            size = rng.randint(120, 280)
            color = rng.choice(['#ffffff', '#c25d3f', '#256f62', '#2f5f8f'])
            draw.ellipse((x, y, x + size, y + size), fill=color, outline=None)

    def draw_hair(self, draw, rng, hair, sex):
        if sex == Profile.Sex.WOMAN and rng.random() > 0.25:
            draw.rounded_rectangle((235, 165, 665, 660), radius=210, fill=hair)
        else:
            draw.pieslice((245, 125, 655, 470), 180, 360, fill=hair)
            draw.rounded_rectangle((255, 240, 645, 385), radius=110, fill=hair)
        draw.ellipse((270, 185, 630, 420), fill=hair)

    def draw_face(self, draw, rng):
        eye_y = rng.randint(375, 395)
        draw.ellipse((360, eye_y, 390, eye_y + 18), fill='#2a2522')
        draw.ellipse((510, eye_y, 540, eye_y + 18), fill='#2a2522')
        draw.arc((410, 405, 490, 500), 15, 165, fill='#946047', width=5)
        draw.arc((380, 470, 520, 545), 20, 160, fill='#8d3d3d', width=7)
        if rng.random() > 0.55:
            draw.arc((335, eye_y - 35, 405, eye_y - 12), 200, 345, fill='#2a2522', width=5)
            draw.arc((495, eye_y - 35, 565, eye_y - 12), 200, 345, fill='#2a2522', width=5)

    def draw_clothes(self, draw, rng, shirt):
        collar = rng.choice(['#f7f4ee', '#e8eef4', '#f4dfd1'])
        draw.polygon([(365, 680), (450, 815), (535, 680)], fill=collar)
        draw.line((450, 815, 450, 1060), fill=self.darker(shirt), width=8)

    def draw_photo_texture(self, image, rng):
        overlay = Image.new('RGBA', image.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        for _ in range(1200):
            x = rng.randint(0, image.width - 1)
            y = rng.randint(0, image.height - 1)
            alpha = rng.randint(4, 14)
            draw.point((x, y), fill=(255, 255, 255, alpha))
        image.alpha_composite(overlay)

    def darker(self, color):
        color = color.lstrip('#')
        r, g, b = (int(color[i:i + 2], 16) for i in (0, 2, 4))
        return f'#{int(r * 0.72):02x}{int(g * 0.72):02x}{int(b * 0.72):02x}'
