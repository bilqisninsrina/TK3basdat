from django.urls import path

from . import views

app_name = 'pengguna'

urlpatterns = [
    path('', views.role_selection, name='role_selection'),
    path('register/customer/', views.register_customer, name='register_customer'),
    path('register/organizer/', views.register_organizer, name='register_organizer'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('artists/', views.artist_list, name='artist_list'),
    path('artists/create/', views.artist_create, name='artist_create'),
    path('artists/<uuid:artist_id>/edit/', views.artist_update, name='artist_update'),
    path('artists/<uuid:artist_id>/delete/', views.artist_delete, name='artist_delete'),
    path('ticket-categories/', views.ticket_category_list, name='ticket_category_list'),
    path('ticket-categories/create/', views.ticket_category_create, name='ticket_category_create'),
    path('ticket-categories/<uuid:category_id>/edit/', views.ticket_category_update, name='ticket_category_update'),
    path('ticket-categories/<uuid:category_id>/delete/', views.ticket_category_delete, name='ticket_category_delete'),
]
