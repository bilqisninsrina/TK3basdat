from django.db import migrations


def refresh_demo_ui_data(apps, schema_editor):
    UserAccount = apps.get_model('pengguna', 'UserAccount')
    Venue = apps.get_model('pengguna', 'Venue')
    Event = apps.get_model('pengguna', 'Event')

    UserAccount.objects.filter(username='admin').update(full_name='Administrator')
    UserAccount.objects.filter(username='organizer1').update(full_name='Andi Wijaya')
    UserAccount.objects.filter(username='customer1').update(full_name='Budi Santoso')

    Venue.objects.filter(venue_name='Jakarta Convention Center').update(has_reserved_seating=True)
    Venue.objects.filter(venue_name='Taman Impian Jayakarta').update(has_reserved_seating=False)
    Venue.objects.filter(venue_name='Bandung Hall Center').update(has_reserved_seating=True)

    Event.objects.filter(event_title='Konser Melodi Senja').update(
        description='Nikmati suasana senja dengan alunan musik indie yang menenangkan.'
    )
    Event.objects.filter(event_title='Festival Seni Budaya').update(
        description='Pertunjukan budaya lintas genre dengan panggung terbuka yang meriah.'
    )
    Event.objects.filter(event_title='Malam Akustik Bandung').update(
        description='Sajian akustik intim dengan tata suara hangat dan penuh cerita.'
    )


def noop(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ('pengguna', '0003_event_description_useraccount_full_name_and_more'),
    ]

    operations = [
        migrations.RunPython(refresh_demo_ui_data, noop),
    ]
