import uuid
from decimal import Decimal

from django.contrib.auth.hashers import check_password, make_password
from django.core.validators import MinValueValidator
from django.db import models


class Role(models.Model):
    role_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role_name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ['role_name']

    def __str__(self):
        return self.role_name.title()


class UserAccount(models.Model):
    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100, blank=True)
    password = models.CharField(max_length=255)

    class Meta:
        ordering = ['username']

    def __str__(self):
        return self.username

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    @property
    def role_name(self):
        role = self.roles.select_related('role').first()
        return role.role.role_name if role else ''

    @property
    def display_name(self):
        if hasattr(self, 'customer_profile'):
            return self.customer_profile.full_name
        if hasattr(self, 'organizer_profile'):
            return self.organizer_profile.organizer_name
        if self.full_name:
            return self.full_name
        return self.username

    @property
    def initial(self):
        return (self.display_name[:1] or '?').upper()


class AccountRole(models.Model):
    account_role_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='accounts')
    user = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='roles')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['role', 'user'], name='unique_account_role')
        ]
        ordering = ['role__role_name', 'user__username']

    def __str__(self):
        return f'{self.user.username} - {self.role.role_name}'


class Customer(models.Model):
    customer_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE, related_name='customer_profile')

    class Meta:
        ordering = ['full_name']

    def __str__(self):
        return self.full_name


class Organizer(models.Model):
    organizer_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organizer_name = models.CharField(max_length=100)
    contact_email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True)
    user = models.OneToOneField(UserAccount, on_delete=models.CASCADE, related_name='organizer_profile')

    class Meta:
        ordering = ['organizer_name']

    def __str__(self):
        return self.organizer_name


class Venue(models.Model):
    venue_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue_name = models.CharField(max_length=100)
    capacity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    address = models.TextField()
    city = models.CharField(max_length=100)
    has_reserved_seating = models.BooleanField(default=False)

    class Meta:
        ordering = ['venue_name']

    def __str__(self):
        return self.venue_name


class Event(models.Model):
    event_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_datetime = models.DateTimeField()
    event_title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='events')
    organizer = models.ForeignKey(Organizer, on_delete=models.CASCADE, related_name='events')

    class Meta:
        ordering = ['event_title']

    def __str__(self):
        return self.event_title


class Artist(models.Model):
    artist_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    genre = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def initials(self):
        return (self.name[:1] or '?').upper()


class EventArtist(models.Model):
    event_artist_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='artist_links')
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='event_links')
    role = models.CharField(max_length=100, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['event', 'artist'], name='unique_event_artist')
        ]

    def __str__(self):
        return f'{self.artist.name} @ {self.event.event_title}'


class TicketCategory(models.Model):
    category_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category_name = models.CharField(max_length=50)
    quota = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0'))],
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ticket_categories')

    class Meta:
        ordering = ['event__event_title', 'category_name']

    def __str__(self):
        return f'{self.category_name} - {self.event.event_title}'
