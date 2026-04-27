from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum

from .models import (
    AccountRole,
    Artist,
    Customer,
    Organizer,
    Role,
    TicketCategory,
    UserAccount,
)


class BaseStyledFormMixin:
    field_class = 'input'

    def apply_base_styles(self):
        for name, field in self.fields.items():
            widget = field.widget
            classes = widget.attrs.get('class', '').split()
            if self.field_class not in classes:
                classes.append(self.field_class)
            widget.attrs['class'] = ' '.join(filter(None, classes))
            widget.attrs.setdefault('autocomplete', 'off')
            if isinstance(widget, forms.PasswordInput):
                widget.attrs['autocomplete'] = 'new-password'


class CustomerRegistrationForm(BaseStyledFormMixin, forms.Form):
    full_name = forms.CharField(label='Nama Lengkap', max_length=100)
    email = forms.EmailField(label='Email')
    phone_number = forms.CharField(label='Nomor Telepon', max_length=20)
    username = forms.CharField(label='Username', max_length=100)
    password = forms.CharField(label='Password', min_length=6, widget=forms.PasswordInput())
    password_confirmation = forms.CharField(
        label='Konfirmasi Password',
        widget=forms.PasswordInput(),
    )
    agree_terms = forms.BooleanField(label='Saya setuju dengan Syarat & Ketentuan')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['full_name'].widget.attrs['placeholder'] = 'Masukkan nama lengkap'
        self.fields['email'].widget.attrs['placeholder'] = 'Masukkan email'
        self.fields['phone_number'].widget.attrs['placeholder'] = 'Masukkan nomor telepon'
        self.fields['username'].widget.attrs['placeholder'] = 'Pilih username'
        self.fields['password'].widget.attrs['placeholder'] = 'Minimal 6 karakter'
        self.fields['password_confirmation'].widget.attrs['placeholder'] = 'Konfirmasi password'
        self.apply_base_styles()
        self.fields['agree_terms'].widget.attrs['class'] = 'checkbox'

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if UserAccount.objects.filter(username__iexact=username).exists():
            raise ValidationError('Username sudah digunakan.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if UserAccount.objects.filter(email__iexact=email).exists():
            raise ValidationError('Email sudah digunakan.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirmation = cleaned_data.get('password_confirmation')
        if password and confirmation and password != confirmation:
            self.add_error('password_confirmation', 'Konfirmasi password tidak sama.')
        return cleaned_data

    @transaction.atomic
    def save(self):
        user = UserAccount(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            full_name=self.cleaned_data['full_name'],
        )
        user.set_password(self.cleaned_data['password'])
        user.save()

        role = Role.objects.get(role_name='customer')
        AccountRole.objects.create(user=user, role=role)
        Customer.objects.create(
            user=user,
            full_name=self.cleaned_data['full_name'],
            phone_number=self.cleaned_data['phone_number'],
        )
        return user


class OrganizerRegistrationForm(BaseStyledFormMixin, forms.Form):
    organizer_name = forms.CharField(label='Nama Lengkap', max_length=100)
    contact_email = forms.EmailField(label='Email')
    phone_number = forms.CharField(label='Nomor Telepon', max_length=20)
    username = forms.CharField(label='Username', max_length=100)
    password = forms.CharField(label='Password', min_length=6, widget=forms.PasswordInput())
    password_confirmation = forms.CharField(
        label='Konfirmasi Password',
        widget=forms.PasswordInput(),
    )
    agree_terms = forms.BooleanField(label='Saya setuju dengan Syarat & Ketentuan')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['organizer_name'].widget.attrs['placeholder'] = 'Masukkan nama lengkap'
        self.fields['contact_email'].widget.attrs['placeholder'] = 'Masukkan email'
        self.fields['phone_number'].widget.attrs['placeholder'] = 'Masukkan nomor telepon'
        self.fields['username'].widget.attrs['placeholder'] = 'Pilih username'
        self.fields['password'].widget.attrs['placeholder'] = 'Minimal 6 karakter'
        self.fields['password_confirmation'].widget.attrs['placeholder'] = 'Konfirmasi password'
        self.apply_base_styles()
        self.fields['agree_terms'].widget.attrs['class'] = 'checkbox'

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if UserAccount.objects.filter(username__iexact=username).exists():
            raise ValidationError('Username sudah digunakan.')
        return username

    def clean_contact_email(self):
        email = self.cleaned_data['contact_email'].strip().lower()
        if UserAccount.objects.filter(email__iexact=email).exists():
            raise ValidationError('Email sudah digunakan.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirmation = cleaned_data.get('password_confirmation')
        if password and confirmation and password != confirmation:
            self.add_error('password_confirmation', 'Konfirmasi password tidak sama.')
        return cleaned_data

    @transaction.atomic
    def save(self):
        user = UserAccount(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['contact_email'],
            full_name=self.cleaned_data['organizer_name'],
        )
        user.set_password(self.cleaned_data['password'])
        user.save()

        role = Role.objects.get(role_name='organizer')
        AccountRole.objects.create(user=user, role=role)
        Organizer.objects.create(
            user=user,
            organizer_name=self.cleaned_data['organizer_name'],
            contact_email=self.cleaned_data['contact_email'],
            phone_number=self.cleaned_data['phone_number'],
        )
        return user


class LoginForm(BaseStyledFormMixin, forms.Form):
    username = forms.CharField(label='Username', max_length=100)
    password = forms.CharField(label='Password', widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'Masukkan username'
        self.fields['password'].widget.attrs['placeholder'] = 'Masukkan password'
        self.apply_base_styles()


class CustomerProfileForm(BaseStyledFormMixin, forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['full_name', 'phone_number']
        labels = {
            'full_name': 'Nama Lengkap',
            'phone_number': 'Nomor Telepon',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_base_styles()


class OrganizerProfileForm(BaseStyledFormMixin, forms.ModelForm):
    class Meta:
        model = Organizer
        fields = ['organizer_name', 'contact_email']
        labels = {
            'organizer_name': 'Nama Organizer',
            'contact_email': 'Contact Email',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_base_styles()


class PasswordUpdateForm(BaseStyledFormMixin, forms.Form):
    old_password = forms.CharField(label='Password Lama', widget=forms.PasswordInput())
    new_password = forms.CharField(label='Password Baru', min_length=6, widget=forms.PasswordInput())
    password_confirmation = forms.CharField(
        label='Konfirmasi Password Baru',
        widget=forms.PasswordInput(),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs['placeholder'] = 'Password Lama'
        self.fields['new_password'].widget.attrs['placeholder'] = 'Password Baru'
        self.fields['password_confirmation'].widget.attrs['placeholder'] = 'Konfirmasi Password Baru'
        self.apply_base_styles()

    def clean_old_password(self):
        old_password = self.cleaned_data['old_password']
        if not self.user.check_password(old_password):
            raise ValidationError('Password lama tidak sesuai.')
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        if (
            cleaned_data.get('new_password')
            and cleaned_data.get('password_confirmation')
            and cleaned_data['new_password'] != cleaned_data['password_confirmation']
        ):
            self.add_error('password_confirmation', 'Konfirmasi password baru tidak sama.')
        return cleaned_data

    def save(self):
        self.user.set_password(self.cleaned_data['new_password'])
        self.user.save(update_fields=['password'])
        return self.user


class ArtistForm(BaseStyledFormMixin, forms.ModelForm):
    class Meta:
        model = Artist
        fields = ['name', 'genre']
        labels = {
            'name': 'Nama Artis',
            'genre': 'Genre',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['placeholder'] = 'cth. Fourtwnty'
        self.fields['genre'].required = False
        self.fields['genre'].widget.attrs['placeholder'] = 'cth. Indie Folk'
        self.apply_base_styles()


class TicketCategoryForm(BaseStyledFormMixin, forms.ModelForm):
    class Meta:
        model = TicketCategory
        fields = ['event', 'category_name', 'price', 'quota']
        labels = {
            'event': 'Acara',
            'category_name': 'Nama Kategori',
            'price': 'Harga (Rp)',
            'quota': 'Kuota',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category_name'].widget.attrs['placeholder'] = 'cth. VVIP'
        self.fields['price'].widget.attrs['placeholder'] = '750000'
        self.fields['quota'].widget.attrs['placeholder'] = '100'
        self.fields['price'].widget.attrs['step'] = '0.01'
        self.fields['quota'].widget.attrs['min'] = '1'
        self.apply_base_styles()

    def clean(self):
        cleaned_data = super().clean()
        event = cleaned_data.get('event')
        quota = cleaned_data.get('quota')
        price = cleaned_data.get('price')
        if price is not None and price < 0:
            self.add_error('price', 'Harga tidak boleh negatif.')
        if quota is not None and quota <= 0:
            self.add_error('quota', 'Kuota harus lebih dari 0.')
        if event and quota:
            current_total = (
                TicketCategory.objects.filter(event=event)
                .exclude(pk=self.instance.pk)
                .aggregate(total=Sum('quota'))
                .get('total')
                or 0
            )
            if current_total + quota > event.venue.capacity:
                self.add_error(
                    'quota',
                    (
                        'Total kuota semua kategori untuk event ini melebihi '
                        f'kapasitas venue ({event.venue.capacity}).'
                    ),
                )
        return cleaned_data
