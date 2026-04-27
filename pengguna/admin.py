from django.contrib import admin

from .models import (
    AccountRole,
    Artist,
    Customer,
    Event,
    EventArtist,
    Organizer,
    Role,
    TicketCategory,
    UserAccount,
    Venue,
)

admin.site.register(Role)
admin.site.register(UserAccount)
admin.site.register(AccountRole)
admin.site.register(Customer)
admin.site.register(Organizer)
admin.site.register(Venue)
admin.site.register(Event)
admin.site.register(Artist)
admin.site.register(EventArtist)
admin.site.register(TicketCategory)
