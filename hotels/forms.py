from django import forms
from .models import RoomReservation, Hotel, RoomType, HotelRoom
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class UserForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")


class HotelForm(forms.ModelForm):
    class Meta:
        model = Hotel
        fields = (
        "name", "location", "image1", "image2", "image3", "image4", "room_types", "description", "free_wifi",
        "fitness_center", "breakfast", "swimming_pool", "rating")


class RoomTypeForm(forms.ModelForm):
    class Meta:
        model = RoomType
        fields = '__all__'


class HotelRoomForm(forms.ModelForm):
    class Meta:
        model = HotelRoom
        fields = ['room_type', 'available_rooms']


class RoomReservationForm(forms.ModelForm):
    class Meta:
        model = RoomReservation
        fields = ['guest_name', 'guest_phone']

    def __init__(self, room_types, *args, **kwargs):
        super(RoomReservationForm, self).__init__(*args, **kwargs)

        for room_type in room_types:
            field_name = f'quantity_{room_type.id}'
            self.fields[field_name] = forms.ChoiceField(
                choices=[(i, i) for i in range(4)],
                label=f'Select Rooms for {room_type.name}',
                widget=forms.Select(attrs={'class': 'room-select'})
            )

    def clean(self):
        cleaned_data = super().clean()
        total_quantity = 0

        for field_name, value in cleaned_data.items():
            if field_name.startswith('quantity_'):
                total_quantity += int(value)

        if total_quantity == 0:
            raise forms.ValidationError("Please select at least one room.")
        return cleaned_data
