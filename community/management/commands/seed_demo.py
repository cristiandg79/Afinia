from datetime import timedelta
from random import Random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import Connection, Profile
from community.models import Group, GroupMembership, Plan, PlanAttendance
from messaging.models import Conversation, Message


class Command(BaseCommand):
    help = 'Creates rich demo data for local development.'

    def handle(self, *args, **options):
        rng = Random(42)

        cities = [
            ('Madrid', 'Madrid'), ('Barcelona', 'Barcelona'), ('Valencia', 'Valencia'),
            ('Sevilla', 'Sevilla'), ('Bilbao', 'Bizkaia'), ('Malaga', 'Malaga'),
            ('Zaragoza', 'Zaragoza'), ('A Coruna', 'A Coruna'), ('Valladolid', 'Valladolid'),
            ('Murcia', 'Murcia'),
        ]
        names = [
            'Lucia', 'Carlos', 'Marta', 'Javier', 'Nerea', 'Pablo', 'Irene', 'Sergio',
            'Amina', 'Hugo', 'Laura', 'Diego', 'Clara', 'Manuel', 'Sara', 'Adrian',
            'Noa', 'Ruben', 'Elena', 'Marcos', 'Nadia', 'Alvaro', 'Paula', 'Ivan',
            'Vera', 'Oscar', 'Carmen', 'Leo', 'Julia', 'Raul', 'Ines', 'Daniel',
            'Teresa', 'Mateo', 'Miriam', 'Tomas', 'Rocio', 'Gael', 'Lidia', 'Andres',
        ]
        interests = ['cafe', 'cinema', 'gaming', 'reading', 'music', 'walks', 'art', 'sports', 'pets', 'support']
        goals = ['friendship', 'dating', 'groups', 'talk']
        social_preferences = ['chat_first', 'small_groups', 'quiet_places', 'clear_plans', 'slow_pace']
        bios = [
            'Me apetece conocer gente sin prisas, para charlar y hacer planes sencillos.',
            'Busco amistades con quien compartir cine, cafés y conversaciones tranquilas.',
            'Prefiero empezar por aquí y quedar cuando haya confianza.',
            'Me gustan los planes pequeños, la música y descubrir sitios accesibles.',
            'Estoy intentando ampliar mi círculo social con personas que entiendan otros ritmos.',
            'Valoro la comunicación clara, el humor y los planes sin demasiada saturación.',
            'Me interesan los grupos donde se pueda hablar y también proponer salidas.',
            'Busco conexiones sanas, ya sea amistad, citas tranquilas o planes en grupo.',
        ]
        accessibility_notes = [
            'Me ayuda que los planes tengan hora y lugar claros.',
            'Prefiero sitios con poco ruido y posibilidad de sentarse.',
            'Necesito saber si el lugar tiene entrada accesible.',
            'Me viene bien hablar antes por chat para sentirme cómoda.',
            '', '',
        ]

        users = []
        for index, name in enumerate(names, start=1):
            city, province = cities[index % len(cities)]
            username = f'demo_{name.lower()}_{index}'
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={'email': f'{username}@afinia.local', 'first_name': name},
            )
            user.set_password('demo12345')
            user.save()

            profile, _ = Profile.objects.get_or_create(user=user, defaults={'display_name': user.username})
            profile.display_name = user.username
            profile.country = 'ES'
            profile.city = city
            profile.province = province
            profile.bio = rng.choice(bios)
            profile.goals = rng.sample(goals, rng.randint(1, 3))
            profile.interests = rng.sample(interests, rng.randint(3, 6))
            profile.social_preferences = rng.sample(social_preferences, rng.randint(2, 4))
            profile.accessibility_notes = rng.choice(accessibility_notes)
            profile.accessibility_visibility = rng.choice(['private', 'connections', 'public'])
            profile.open_to_nearby = True
            profile.open_to_online = rng.choice([True, True, False])
            profile.onboarding_completed = True
            profile.save()
            users.append(user)

        demo_user = User.objects.filter(username='demo').first()
        if demo_user:
            users.insert(0, demo_user)

        group_specs = [
            ('Madrid planes tranquilos', 'Madrid', 'Planes tranquilos', 'Cafés, paseos cortos y actividades con poca saturación.'),
            ('Barcelona cine y charla', 'Barcelona', 'Cine y series', 'Quedadas para ver películas, comentar series y tomar algo después.'),
            ('Valencia paseos accesibles', 'Valencia', 'Paseos', 'Rutas urbanas suaves y lugares con buena accesibilidad.'),
            ('Sevilla café sin prisas', 'Sevilla', 'Café', 'Grupo para conversaciones tranquilas y nuevas amistades.'),
            ('Bilbao lectura compartida', 'Bilbao', 'Lectura', 'Libros, cómics, poesía y recomendaciones con calma.'),
            ('Málaga ocio inclusivo', 'Málaga', 'Ocio', 'Planes variados pensando en accesibilidad y ritmo social.'),
            ('Gaming online Afinia', '', 'Videojuegos', 'Partidas online y comunidad tranquila.'),
            ('Arte y museos accesibles', 'Madrid', 'Arte', 'Museos, exposiciones y planes culturales con información previa.'),
            ('Apoyo entre iguales', '', 'Apoyo social', 'Espacio social para hablar de vivencias sin convertirlo en terapia.'),
            ('Amistades 30+', '', 'Amistad', 'Personas adultas buscando ampliar círculo social.'),
            ('Citas con calma', '', 'Citas', 'Para quienes quieren conocer a alguien sin dinámicas agresivas.'),
            ('Planes pequeños', '', 'Grupos pequeños', 'Actividades con pocas plazas y ambiente tranquilo.'),
        ]

        groups = []
        for index, (name, city, topic, description) in enumerate(group_specs):
            owner = users[index % len(users)]
            group, _ = Group.objects.get_or_create(
                name=name,
                defaults={'description': description, 'country': 'ES', 'city': city, 'topic': topic, 'created_by': owner},
            )
            group.description = description
            group.country = 'ES'
            group.city = city
            group.topic = topic
            group.privacy = rng.choice(['open', 'request', 'request'])
            group.created_by = owner
            group.save()
            GroupMembership.objects.get_or_create(group=group, user=owner, defaults={'status': 'moderator'})
            for member in rng.sample(users, min(len(users), rng.randint(8, 18))):
                GroupMembership.objects.get_or_create(
                    group=group,
                    user=member,
                    defaults={'status': rng.choice(['approved', 'approved', 'pending'])},
                )
            groups.append(group)

        plan_titles = [
            'Café tranquilo de bienvenida', 'Paseo corto por zona accesible', 'Tarde de juegos de mesa',
            'Cine y charla después', 'Visita a exposición con poca prisa', 'Quedada online para presentarnos',
            'Merienda en grupo pequeño', 'Club de lectura ligero', 'Ruta urbana suave', 'Plan de domingo sin ruido',
            'Taller creativo informal', 'Charla de música y recomendaciones', 'Videojuegos cooperativos online',
            'Encuentro para nuevas amistades', 'Cita grupal de café', 'Museo con entrada accesible',
            'Picnic tranquilo en parque', 'Paseo fotográfico',
        ]
        places = ['Centro', 'Biblioteca municipal', 'Café accesible', 'Parque urbano', 'Centro cultural', 'Online']
        for index, title in enumerate(plan_titles):
            group = groups[index % len(groups)]
            city = group.city or rng.choice(cities)[0]
            plan, _ = Plan.objects.get_or_create(
                title=f'{title} #{index + 1}',
                defaults={
                    'description': 'Plan pensado para conocerse con calma, con información previa y grupo reducido.',
                    'group': group,
                    'country': group.country,
                    'city': city,
                    'place': rng.choice(places),
                    'starts_at': timezone.now() + timedelta(days=index + 2, hours=rng.randint(0, 8)),
                    'capacity': rng.randint(5, 14),
                    'mood': rng.choice(['calm', 'social', 'outdoor', 'online']),
                    'accessibility_info': rng.choice([
                        'Se confirmará accesibilidad antes de cerrar el lugar.',
                        'Lugar con entrada accesible y opción de sentarse.',
                        'Ambiente previsto de ruido bajo o moderado.',
                        'Plan online, sin desplazamiento.',
                    ]),
                    'created_by': group.created_by,
                },
            )
            for attendee in rng.sample(users, min(len(users), rng.randint(4, 10))):
                PlanAttendance.objects.get_or_create(
                    plan=plan,
                    user=attendee,
                    defaults={'status': rng.choice(['approved', 'approved', 'requested'])},
                )

        for requester, receiver in zip(users[1:18], users[2:19]):
            if requester == receiver:
                continue
            connection, created = Connection.objects.get_or_create(
                requester=requester,
                receiver=receiver,
                defaults={'status': rng.choice(['accepted', 'pending', 'accepted'])},
            )
            if created and connection.status == 'accepted':
                conversation = Conversation.objects.create()
                conversation.participants.add(requester, receiver)
                Message.objects.create(
                    conversation=conversation,
                    sender=requester,
                    body='Hola, he visto tu perfil y creo que tenemos intereses parecidos.',
                )
                Message.objects.create(
                    conversation=conversation,
                    sender=receiver,
                    body='Gracias por escribir. Me apetece hablar con calma.',
                )

        self.stdout.write(self.style.SUCCESS(
            f'Demo ready: {User.objects.count()} users, {Group.objects.count()} groups, {Plan.objects.count()} plans.'
        ))
