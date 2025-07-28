from django.urls import path
from .views import booking_view, booking_list, get_available_times, cancel_booking
from django.contrib.auth.views import LogoutView


urlpatterns = [
    path('', booking_view, name='booking_form'),
    path('panel/', booking_list, name='booking_list'),
    path('accounts/logout/', LogoutView.as_view(), name='logout'),
    path('get_available_times/', get_available_times, name='get_available_times'),
    path('cancel_booking/<int:booking_id>', cancel_booking, name='cancel_booking'),
]
