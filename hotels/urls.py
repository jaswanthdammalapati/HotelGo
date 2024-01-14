from django.urls import path
from .views import homepage, user_login, user_register, user_logout, hotel_detail, hotels, ReserveRoomView, \
    reservation_success, my_reservation, hotel_upload, add_room_type, manage_rooms, update_available_rooms, edit_hotel, \
    delete_hotel, reservation_list
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
                  path('', homepage, name='homepage'),
                  path('register', user_register, name='register'),
                  path("login", user_login, name="login"),
                  path("logout", user_logout, name="logout"),
                  path('hotels/', hotels, name='hotels'),
                  path('hotel/<int:hotel_id>/', hotel_detail, name='hotel_detail'),
                  path('reserve-room/<int:hotel_id>/', ReserveRoomView.as_view(), name='reserve_room'),
                  path('reserve-room/success/', reservation_success, name='reservation_success'),
                  path('reservations/', my_reservation, name='my_reservation'),
                  path('hotel/upload/', hotel_upload, name='hotel_upload'),
                  path('add-room-type/', add_room_type, name='add_room_type'),
                  path('manage-rooms/<int:hotel_id>/', manage_rooms, name='manage_rooms'),
                  path('update-available-rooms/<int:hotel_id>/', update_available_rooms, name='update_available_rooms'),
                  path('hotel/edit/<int:hotel_id>/', edit_hotel, name='edit_hotel'),
                  path('hotel/delete/<int:hotel_id>/', delete_hotel, name='delete_hotel'),
                  path('reservation_list/<int:hotel_id>/', reservation_list, name='reservation_list')

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
