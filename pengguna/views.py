from decimal import Decimal

from django.contrib import messages
from django.db.models import Count, Max, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    ArtistForm,
    CustomerProfileForm,
    CustomerRegistrationForm,
    LoginForm,
    OrganizerProfileForm,
    OrganizerRegistrationForm,
    PasswordUpdateForm,
    TicketCategoryForm,
)
from .models import Artist, Event, EventArtist, TicketCategory, UserAccount, Venue
from .utils import build_base_context, ensure_logged_in, ensure_roles, get_current_user


def render_page(request, template_name, context=None, status=200):
    payload = build_base_context(request)
    if context:
        payload.update(context)
    return render(request, template_name, payload, status=status)


def format_currency(value):
    amount = Decimal(value or 0)
    return f"Rp {amount:,.0f}".replace(',', '.')


def format_short_currency(value):
    amount = float(value or 0)
    if amount >= 1_000_000_000:
        return f"Rp {amount / 1_000_000_000:.1f}B"
    if amount >= 1_000_000:
        return f"Rp {amount / 1_000_000:.1f}M"
    if amount >= 1_000:
        return f"Rp {amount / 1_000:.0f}K"
    return f"Rp {amount:.0f}"


def format_integer(value):
    return f"{int(value or 0):,}".replace(',', '.')


def role_selection(request):
    if get_current_user(request):
        return redirect('pengguna:dashboard')
    return render_page(request, 'pengguna/role_selection.html', {'hide_navbar': True})


def register_customer(request):
    if get_current_user(request):
        return redirect('pengguna:dashboard')
    form = CustomerRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Akun pelanggan berhasil dibuat. Silakan login.')
        return redirect('pengguna:login')
    return render_page(
        request,
        'pengguna/register.html',
        {
            'page_title': 'Daftar sebagai Pelanggan',
            'subtitle': 'Buat akun baru untuk memulai pengalaman Anda',
            'back_url': 'pengguna:role_selection',
            'form': form,
            'hide_navbar': True,
        },
    )


def register_organizer(request):
    if get_current_user(request):
        return redirect('pengguna:dashboard')
    form = OrganizerRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Akun penyelenggara berhasil dibuat. Silakan login.')
        return redirect('pengguna:login')
    return render_page(
        request,
        'pengguna/register.html',
        {
            'page_title': 'Daftar sebagai Penyelenggara',
            'subtitle': 'Buat akun baru untuk memulai pengalaman Anda',
            'back_url': 'pengguna:role_selection',
            'form': form,
            'hide_navbar': True,
        },
    )


def login_view(request):
    if get_current_user(request):
        return redirect('pengguna:dashboard')
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        try:
            user = UserAccount.objects.prefetch_related('roles__role').get(username__iexact=username)
        except UserAccount.DoesNotExist:
            user = None

        if not user or not user.check_password(password):
            messages.error(request, 'Username atau password salah.')
        else:
            request.session['user_id'] = str(user.user_id)
            request.session['role_name'] = user.role_name
            messages.success(request, f'Selamat datang, {user.display_name}.')
            return redirect('pengguna:dashboard')

    return render_page(
        request,
        'pengguna/login.html',
        {
            'page_title': 'Masuk ke Akun Anda',
            'subtitle': 'Gunakan kredensial Anda untuk mengakses platform',
            'form': form,
            'hide_navbar': True,
        },
    )


def logout_view(request):
    request.session.flush()
    messages.success(request, 'Anda berhasil logout.')
    return redirect('pengguna:login')


def dashboard(request):
    gate = ensure_logged_in(request)
    if gate:
        return gate

    user = get_current_user(request)
    role_name = user.role_name

    if role_name == 'admin':
        context = _build_admin_dashboard_context()
    elif role_name == 'organizer':
        context = _build_organizer_dashboard_context(user)
    else:
        context = _build_customer_dashboard_context(user)

    return render_page(request, 'pengguna/dashboard.html', context)


def _build_admin_dashboard_context():
    total_users = UserAccount.objects.count()
    total_events = Event.objects.count()
    total_quota = TicketCategory.objects.aggregate(total=Sum('quota')).get('total') or 0
    total_value = sum(category.price * category.quota for category in TicketCategory.objects.select_related('event'))
    total_venues = Venue.objects.count()
    reserved_count = Venue.objects.filter(has_reserved_seating=True).count()
    largest_capacity = Venue.objects.aggregate(capacity=Max('capacity')).get('capacity') or 0

    stats = [
        {
            'label': 'Total Pengguna',
            'value': format_integer(total_users),
            'note': 'Pengguna aktif',
            'icon': 'users',
            'tone': 'blue',
        },
        {
            'label': 'Total Acara',
            'value': format_integer(total_events),
            'note': 'Acara terdaftar',
            'icon': 'calendar',
            'tone': 'green',
        },
        {
            'label': 'Omzet Platform',
            'value': format_short_currency(total_value),
            'note': 'Gross volume',
            'icon': 'chart',
            'tone': 'purple',
        },
        {
            'label': 'Promosi Aktif',
            'value': '3',
            'note': 'Running campaigns',
            'icon': 'ticket',
            'tone': 'orange',
        },
    ]

    admin_panels = [
        {
            'title': 'Infrastruktur Venue',
            'link_text': 'Ringkasan',
            'rows': [
                ('Total Venue Terdaftar', f'{total_venues} Lokasi'),
                ('Reserved Seating', f'{reserved_count} Venue'),
                ('Kapasitas Terbesar', f'{format_integer(largest_capacity)} Kursi'),
            ],
            'button_label': 'Kelola Venue',
        },
        {
            'title': 'Marketing & Promosi',
            'link_text': 'Ringkasan',
            'rows': [
                ('Promo Persentase', '1 Aktif'),
                ('Promo Potongan Nominal', '1 Aktif'),
                ('Total Penggunaan', format_integer(total_quota)),
            ],
            'button_label': 'Kelola Promosi',
        },
    ]

    return {
        'dashboard_variant': 'admin',
        'hero_eyebrow': 'Administrator',
        'hero_title': 'System Console',
        'hero_subtitle': 'Pantau dan kelola platform TikTakTuk',
        'hero_actions': [{'label': 'Promosi', 'style': 'light', 'href': None}],
        'stats': stats,
        'admin_panels': admin_panels,
    }


def _build_organizer_dashboard_context(user):
    events = list(
        user.organizer_profile.events.select_related('venue').prefetch_related('ticket_categories').order_by('event_datetime')
    )
    total_ticket_quota = sum(
        event.ticket_categories.aggregate(total=Sum('quota')).get('total') or 0
        for event in events
    )
    revenue = sum(
        sum(category.price * category.quota for category in event.ticket_categories.all())
        for event in events
    )
    stats = [
        {
            'label': 'Acara Aktif',
            'value': str(len(events)),
            'note': 'Dalam koordinasi',
            'icon': 'calendar',
            'tone': 'blue',
        },
        {
            'label': 'Tiket Terjual',
            'value': format_integer(total_ticket_quota),
            'note': 'Total terjual',
            'icon': 'ticket',
            'tone': 'green',
        },
        {
            'label': 'Revenue',
            'value': format_short_currency(revenue),
            'note': 'Bulan ini',
            'icon': 'chart',
            'tone': 'purple',
        },
        {
            'label': 'Venue Mitra',
            'value': str(len({event.venue_id for event in events})),
            'note': 'Lokasi aktif',
            'icon': 'location',
            'tone': 'orange',
        },
    ]

    performance_items = []
    for event in events:
        quota_total = event.ticket_categories.aggregate(total=Sum('quota')).get('total') or 0
        ratio = min(round((quota_total / event.venue.capacity) * 100), 100) if event.venue.capacity else 0
        performance_items.append(
            {
                'title': event.event_title,
                'badge': 'LIVE',
                'meta': f'{ratio}% terjual',
                'location': event.venue.venue_name,
            }
        )

    return {
        'dashboard_variant': 'organizer',
        'hero_eyebrow': 'Dashboard Penyelenggara',
        'hero_title': user.organizer_profile.organizer_name,
        'hero_subtitle': f'Kelola {len(events)} acara aktif Anda',
        'hero_actions': [
            {'label': 'Kelola Acara', 'style': 'light', 'href': None},
            {'label': 'Venue', 'style': 'muted-dark', 'href': None},
        ],
        'stats': stats,
        'section_title': 'Performa Acara',
        'section_subtitle': 'Status acara yang Anda kelola',
        'section_link': {'label': 'Lihat Semua', 'href': None},
        'event_items': performance_items,
    }


def _build_customer_dashboard_context(user):
    customer_feed = list(
        TicketCategory.objects.select_related('event', 'event__venue').order_by('event__event_datetime', 'category_name')
    )
    upcoming_categories = customer_feed[:4]
    followed_events = {category.event_id for category in customer_feed}
    spending_estimate = sum(category.price for category in upcoming_categories)
    stats = [
        {
            'label': 'Tiket Aktif',
            'value': str(len(upcoming_categories)),
            'note': 'Siap digunakan',
            'icon': 'ticket',
            'tone': 'blue',
        },
        {
            'label': 'Acara Diikuti',
            'value': str(len(followed_events)),
            'note': 'Total pengalaman',
            'icon': 'calendar',
            'tone': 'green',
        },
        {
            'label': 'Kode Promo',
            'value': '3',
            'note': 'Tersedia untuk Anda',
            'icon': 'chart',
            'tone': 'purple',
        },
        {
            'label': 'Total Belanja',
            'value': format_short_currency(spending_estimate),
            'note': 'Bulan ini',
            'icon': 'music',
            'tone': 'orange',
        },
    ]

    ticket_items = [
        {
            'title': category.event.event_title,
            'badge': category.category_name,
            'meta': category.event.event_datetime.strftime('%d %b %Y'),
            'location': category.event.venue.venue_name,
        }
        for category in upcoming_categories
    ]

    return {
        'dashboard_variant': 'customer',
        'hero_eyebrow': 'Selamat datang kembali',
        'hero_title': user.customer_profile.full_name,
        'hero_subtitle': f'{len(followed_events)} acara menarik menunggu Anda',
        'hero_actions': [{'label': 'Cari Tiket', 'style': 'light', 'href': 'pengguna:ticket_category_list'}],
        'stats': stats,
        'section_title': 'Tiket Mendatang',
        'section_subtitle': 'Tiket pertunjukan yang akan datang',
        'section_link': {'label': 'Lihat Semua', 'href': 'pengguna:ticket_category_list'},
        'event_items': ticket_items,
    }


def profile_view(request):
    gate = ensure_logged_in(request)
    if gate:
        return gate

    user = get_current_user(request)
    role_name = user.role_name
    edit_mode = request.GET.get('edit') == '1'

    if role_name == 'customer':
        profile_form = CustomerProfileForm(request.POST or None, instance=user.customer_profile, prefix='profile')
        info_items = [
            {'label': 'Nama Lengkap', 'value': user.customer_profile.full_name, 'icon': 'person'},
            {'label': 'Username', 'value': f'@{user.username}', 'icon': 'at'},
            {'label': 'Nomor Telepon', 'value': user.customer_profile.phone_number, 'icon': 'phone'},
        ]
        role_badge = 'Pelanggan'
    elif role_name == 'organizer':
        profile_form = OrganizerProfileForm(request.POST or None, instance=user.organizer_profile, prefix='profile')
        info_items = [
            {'label': 'Nama Organizer', 'value': user.organizer_profile.organizer_name, 'icon': 'building'},
            {'label': 'Username', 'value': f'@{user.username}', 'icon': 'at'},
            {'label': 'Contact Email', 'value': user.organizer_profile.contact_email, 'icon': 'mail'},
        ]
        role_badge = 'Penyelenggara'
    else:
        profile_form = None
        info_items = [
            {'label': 'Nama Admin', 'value': user.display_name, 'icon': 'person'},
            {'label': 'Username', 'value': f'@{user.username}', 'icon': 'at'},
            {'label': 'Email', 'value': user.email, 'icon': 'mail'},
        ]
        role_badge = 'Administrator'

    password_form = PasswordUpdateForm(user, request.POST or None, prefix='password')

    if request.method == 'POST':
        if 'save_profile' in request.POST and profile_form is not None:
            if profile_form.is_valid():
                profile = profile_form.save(commit=False)
                if role_name == 'customer':
                    user.full_name = profile.full_name
                elif role_name == 'organizer':
                    user.full_name = profile.organizer_name
                user.save(update_fields=['full_name'])
                profile.save()
                messages.success(request, 'Profil berhasil diperbarui.')
                return redirect('pengguna:profile')
            edit_mode = True
        elif 'change_password' in request.POST:
            if password_form.is_valid():
                password_form.save()
                messages.success(request, 'Password berhasil diperbarui.')
                return redirect('pengguna:profile')

    return render_page(
        request,
        'pengguna/profile.html',
        {
            'profile_title': 'Profil Saya',
            'profile_subtitle': 'Kelola informasi pribadi dan preferensi akun Anda',
            'role_badge': role_badge,
            'display_name': user.display_name,
            'initial': user.initial,
            'info_items': info_items,
            'profile_form': profile_form,
            'password_form': password_form,
            'edit_mode': edit_mode,
        },
    )


def artist_list(request):
    base = build_base_context(request)
    query = request.GET.get('q', '').strip()
    artists = Artist.objects.annotate(event_count=Count('event_links__event', distinct=True)).order_by('name')
    if query:
        artists = artists.filter(Q(name__icontains=query) | Q(genre__icontains=query))

    artist_list_items = list(artists)
    for artist in artist_list_items:
        artist.action_allowed = base['is_admin']

    context = {
        'page_heading': 'Daftar Artis',
        'page_subtitle': 'Kelola artis yang ada di platform TikTakTuk',
        'artists': artist_list_items,
        'search_query': query,
        'results_count': len(artist_list_items),
        'total_artists': Artist.objects.count(),
        'genre_count': Artist.objects.exclude(genre='').values('genre').distinct().count(),
        'event_presence_count': Artist.objects.filter(event_links__isnull=False).distinct().count(),
        'show_actions': base['is_admin'],
        'active_modal': None,
        'artist_form': ArtistForm(),
        'delete_target': None,
    }
    return render_page(request, 'pengguna/artist_list.html', context)


def artist_create(request):
    gate = ensure_roles(request, 'admin')
    if gate:
        return gate
    form = ArtistForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Artis baru berhasil ditambahkan.')
        return redirect('pengguna:artist_list')
    return _render_artist_modal(request, 'create', form=form)


def artist_update(request, artist_id):
    gate = ensure_roles(request, 'admin')
    if gate:
        return gate
    artist = get_object_or_404(Artist, pk=artist_id)
    form = ArtistForm(request.POST or None, instance=artist)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Data artis berhasil diperbarui.')
        return redirect('pengguna:artist_list')
    return _render_artist_modal(request, 'edit', form=form, target=artist)


def artist_delete(request, artist_id):
    gate = ensure_roles(request, 'admin')
    if gate:
        return gate
    artist = get_object_or_404(Artist, pk=artist_id)
    if request.method == 'POST':
        artist.delete()
        messages.success(request, 'Artis berhasil dihapus.')
        return redirect('pengguna:artist_list')
    return _render_artist_modal(request, 'delete', target=artist)


def _render_artist_modal(request, mode, form=None, target=None):
    query = request.GET.get('q', '').strip()
    artists = Artist.objects.annotate(event_count=Count('event_links__event', distinct=True)).order_by('name')
    if query:
        artists = artists.filter(Q(name__icontains=query) | Q(genre__icontains=query))

    return render_page(
        request,
        'pengguna/artist_list.html',
        {
            'page_heading': 'Daftar Artis',
            'page_subtitle': 'Kelola artis yang ada di platform TikTakTuk',
            'artists': list(artists),
            'search_query': query,
            'results_count': artists.count(),
            'total_artists': Artist.objects.count(),
            'genre_count': Artist.objects.exclude(genre='').values('genre').distinct().count(),
            'event_presence_count': Artist.objects.filter(event_links__isnull=False).distinct().count(),
            'show_actions': True,
            'active_modal': mode,
            'artist_form': form or ArtistForm(instance=target),
            'delete_target': target,
        },
        status=400 if form is not None and form.errors else 200,
    )


def ticket_category_list(request):
    base = build_base_context(request)
    search_query = request.GET.get('q', '').strip()
    selected_event = request.GET.get('event', '').strip()
    categories = TicketCategory.objects.select_related('event', 'event__venue').order_by('event__event_title', 'category_name')
    if search_query:
        categories = categories.filter(
            Q(category_name__icontains=search_query) | Q(event__event_title__icontains=search_query)
        )
    if selected_event:
        categories = categories.filter(event_id=selected_event)

    category_items = list(categories)
    for category in category_items:
        category.display_price = format_currency(category.price)

    totals = TicketCategory.objects.aggregate(
        total_categories=Count('category_id'),
        total_quota=Sum('quota'),
        highest_price=Max('price'),
    )
    context = {
        'page_heading': 'Kategori Tiket',
        'page_subtitle': 'Kelola kategori dan harga tiket per acara',
        'categories': category_items,
        'events': Event.objects.order_by('event_title'),
        'selected_event': selected_event,
        'search_query': search_query,
        'results_count': len(category_items),
        'total_categories': totals['total_categories'] or 0,
        'total_quota': format_integer(totals['total_quota'] or 0),
        'highest_price': format_currency(totals['highest_price'] or 0),
        'show_actions': base['is_admin'] or base['is_organizer'],
        'active_modal': None,
        'category_form': TicketCategoryForm(),
        'delete_target': None,
    }
    return render_page(request, 'pengguna/ticket_category_list.html', context)


def ticket_category_create(request):
    gate = ensure_roles(request, 'admin', 'organizer')
    if gate:
        return gate
    form = TicketCategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Kategori tiket berhasil ditambahkan.')
        return redirect('pengguna:ticket_category_list')
    return _render_ticket_category_modal(request, 'create', form=form)


def ticket_category_update(request, category_id):
    gate = ensure_roles(request, 'admin', 'organizer')
    if gate:
        return gate
    category = get_object_or_404(TicketCategory, pk=category_id)
    form = TicketCategoryForm(request.POST or None, instance=category)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Kategori tiket berhasil diperbarui.')
        return redirect('pengguna:ticket_category_list')
    return _render_ticket_category_modal(request, 'edit', form=form, target=category)


def ticket_category_delete(request, category_id):
    gate = ensure_roles(request, 'admin', 'organizer')
    if gate:
        return gate
    category = get_object_or_404(TicketCategory, pk=category_id)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Kategori tiket berhasil dihapus.')
        return redirect('pengguna:ticket_category_list')
    return _render_ticket_category_modal(request, 'delete', target=category)


def _render_ticket_category_modal(request, mode, form=None, target=None):
    search_query = request.GET.get('q', '').strip()
    selected_event = request.GET.get('event', '').strip()
    categories = TicketCategory.objects.select_related('event', 'event__venue').order_by('event__event_title', 'category_name')
    if search_query:
        categories = categories.filter(
            Q(category_name__icontains=search_query) | Q(event__event_title__icontains=search_query)
        )
    if selected_event:
        categories = categories.filter(event_id=selected_event)

    category_items = list(categories)
    for category in category_items:
        category.display_price = format_currency(category.price)

    totals = TicketCategory.objects.aggregate(
        total_categories=Count('category_id'),
        total_quota=Sum('quota'),
        highest_price=Max('price'),
    )

    return render_page(
        request,
        'pengguna/ticket_category_list.html',
        {
            'page_heading': 'Kategori Tiket',
            'page_subtitle': 'Kelola kategori dan harga tiket per acara',
            'categories': category_items,
            'events': Event.objects.order_by('event_title'),
            'selected_event': selected_event,
            'search_query': search_query,
            'results_count': len(category_items),
            'total_categories': totals['total_categories'] or 0,
            'total_quota': format_integer(totals['total_quota'] or 0),
            'highest_price': format_currency(totals['highest_price'] or 0),
            'show_actions': True,
            'active_modal': mode,
            'category_form': form or TicketCategoryForm(instance=target),
            'delete_target': target,
        },
        status=400 if form is not None and form.errors else 200,
    )
