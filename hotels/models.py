from django.db import models
from django.shortcuts import render
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from datetime import datetime


class RoomType(models.Model):
    name = models.CharField(max_length=255)
    capacity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return self.name


class HotelRoom(models.Model):
    hotel = models.ForeignKey('Hotel', on_delete=models.CASCADE)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE)
    available_rooms = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.hotel.name} - {self.room_type.name} ({self.available_rooms} available)"


class Hotel(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    image1 = models.ImageField(upload_to='images/hotel_images/')
    image2 = models.ImageField(upload_to='images/hotel_images/', null=True, blank=True)
    image3 = models.ImageField(upload_to='images/hotel_images/', null=True, blank=True)
    image4 = models.ImageField(upload_to='images/hotel_images/', null=True, blank=True)

    room_types = models.ManyToManyField(RoomType, through=HotelRoom)
    description = models.TextField()
    free_wifi = models.BooleanField(default=False)
    fitness_center = models.BooleanField(default=False)
    breakfast = models.BooleanField(default=False)
    swimming_pool = models.BooleanField(default=False)
    rating = models.FloatField()

    def __str__(self):
        return self.name


class RoomReservation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    guest_name = models.CharField(max_length=255)
    guest_email = models.EmailField()
    guest_phone = models.CharField(max_length=15)
    checkin_date = models.DateField(default=datetime.now)
    checkout_date = models.DateField(default=datetime.now)
    booked_on = models.DateTimeField(auto_now_add=True)
    num_days = models.PositiveIntegerField(default=1)
    cost = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.guest_name}'s Reservation for {self.quantity} {self.room_type.name}(s) at {self.hotel.name}"
