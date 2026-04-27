from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.hashers import make_password
from django.db import migrations
from django.utils import timezone


def seed_demo_data(apps, schema_editor):
    Role = apps.get_model('pengguna', 'Role')
    UserAccount = apps.get_model('pengguna', 'UserAccount')
    AccountRole = apps.get_model('pengguna', 'AccountRole')
    Customer = apps.get_model('pengguna', 'Customer')
    Organizer = apps.get_model('pengguna', 'Organizer')
    Venue = apps.get_model('pengguna', 'Venue')
    Event = apps.get_model('pengguna', 'Event')
    Artist = apps.get_model('pengguna', 'Artist')
    EventArtist = apps.get_model('pengguna', 'EventArtist')
    TicketCategory = apps.get_model('pengguna', 'TicketCategory')

    admin_role, _ = Role.objects.get_or_create(role_name='admin')
    organizer_role, _ = Role.objects.get_or_create(role_name='organizer')
    customer_role, _ = Role.objects.get_or_create(role_name='customer')

    admin_user, _ = UserAccount.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@tiktaktuk.local',
            'password': make_password('admin123'),
        },
    )
    organizer_user, _ = UserAccount.objects.get_or_create(
        username='organizer1',
        defaults={
            'email': 'organizer1@example.com',
            'password': make_password('organizer123'),
        },
    )
    customer_user, _ = UserAccount.objects.get_or_create(
        username='customer1',
        defaults={
            'email': 'customer1@example.com',
            'password': make_password('customer123'),
        },
    )

    AccountRole.objects.get_or_create(user=admin_user, role=admin_role)
    AccountRole.objects.get_or_create(user=organizer_user, role=organizer_role)
    AccountRole.objects.get_or_create(user=customer_user, role=customer_role)

    organizer, _ = Organizer.objects.get_or_create(
        user=organizer_user,
        defaults={
            'organizer_name': 'Andi Wijaya',
            'contact_email': 'organizer1@example.com',
            'phone_number': '+628123456789',
        },
    )
    Customer.objects.get_or_create(
        user=customer_user,
        defaults={
            'full_name': 'Budi Santoso',
            'phone_number': '+628123456780',
        },
    )

    venues = [
        ('Jakarta Convention Center', 1000, 'Jl. Gatot Subroto No.1', 'Jakarta'),
        ('Taman Impian Jayakarta', 1200, 'Jl. Taman Impian No.7', 'Jakarta'),
        ('Bandung Hall Center', 800, 'Jl. Braga No.18', 'Bandung'),
    ]
    venue_map = {}
    for venue_name, capacity, address, city in venues:
        venue, _ = Venue.objects.get_or_create(
            venue_name=venue_name,
            defaults={'capacity': capacity, 'address': address, 'city': city},
        )
        venue_map[venue_name] = venue

    now = timezone.now()
    events_data = [
        ('Konser Melodi Senja', now + timedelta(days=20), 'Jakarta Convention Center'),
        ('Festival Seni Budaya', now + timedelta(days=35), 'Taman Impian Jayakarta'),
        ('Malam Akustik Bandung', now + timedelta(days=50), 'Bandung Hall Center'),
    ]
    event_map = {}
    for title, when, venue_name in events_data:
        event, _ = Event.objects.get_or_create(
            event_title=title,
            defaults={
                'event_datetime': when,
                'venue': venue_map[venue_name],
                'organizer': organizer,
            },
        )
        event_map[title] = event

    artists_data = [
        ('Fourtwnty', 'Indie Folk'),
        ('Hindia', 'Indie Pop'),
        ('Tulus', 'Pop'),
        ('Nadin Amizah', 'Folk'),
        ('Pamungkas', 'Singer-Songwriter'),
        ('Raisa', 'R&B / Pop'),
    ]
    artist_map = {}
    for name, genre in artists_data:
        artist, _ = Artist.objects.get_or_create(name=name, defaults={'genre': genre})
        if not artist.genre:
            artist.genre = genre
            artist.save(update_fields=['genre'])
        artist_map[name] = artist

    event_artist_links = [
        ('Konser Melodi Senja', 'Fourtwnty'),
        ('Konser Melodi Senja', 'Hindia'),
        ('Festival Seni Budaya', 'Tulus'),
        ('Festival Seni Budaya', 'Nadin Amizah'),
        ('Malam Akustik Bandung', 'Pamungkas'),
        ('Malam Akustik Bandung', 'Raisa'),
    ]
    for event_title, artist_name in event_artist_links:
        EventArtist.objects.get_or_create(
            event=event_map[event_title],
            artist=artist_map[artist_name],
            defaults={'role': 'Main Artist'},
        )

    categories = [
        ('Konser Melodi Senja', 'VVIP', 50, Decimal('1500000')),
        ('Konser Melodi Senja', 'VIP', 150, Decimal('750000')),
        ('Konser Melodi Senja', 'Category 1', 300, Decimal('450000')),
        ('Konser Melodi Senja', 'Category 2', 500, Decimal('250000')),
        ('Festival Seni Budaya', 'General Admission', 500, Decimal('150000')),
        ('Malam Akustik Bandung', 'VVIP', 30, Decimal('2000000')),
        ('Malam Akustik Bandung', 'VIP', 100, Decimal('900000')),
        ('Malam Akustik Bandung', 'Regular', 400, Decimal('350000')),
    ]
    for event_title, category_name, quota, price in categories:
        TicketCategory.objects.get_or_create(
            event=event_map[event_title],
            category_name=category_name,
            defaults={'quota': quota, 'price': price},
        )


def clear_demo_data(apps, schema_editor):
    Role = apps.get_model('pengguna', 'Role')
    UserAccount = apps.get_model('pengguna', 'UserAccount')
    Role.objects.filter(role_name__in=['admin', 'organizer', 'customer']).delete()
    UserAccount.objects.filter(username__in=['admin', 'organizer1', 'customer1']).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('pengguna', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_demo_data, clear_demo_data),
    ]
