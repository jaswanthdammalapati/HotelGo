from django.contrib import admin
from .models import Hotel, RoomType, HotelRoom, RoomReservation

admin.site.register(Hotel)
admin.site.register(RoomType)
admin.site.register(HotelRoom)
admin.site.register(RoomReservation)

