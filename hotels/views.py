from datetime import datetime
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from .forms import RoomReservationForm, UserForm, HotelForm, RoomTypeForm, HotelRoomForm
from .models import Hotel, RoomType, RoomReservation, HotelRoom
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.core.mail import send_mail
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist


def homepage(request):
    return render(request, 'homepage.html')


def hotel_detail(request, hotel_id):
    hotel = get_object_or_404(Hotel, pk=hotel_id)
    hotel_rooms = HotelRoom.objects.filter(hotel=hotel)
    room_form = HotelRoomForm()
    checkin_date = request.GET.get('checkin_date') or request.session.get('checkin_date', '')
    checkout_date = request.GET.get('checkout_date') or request.session.get('checkout_date', '')
    adults = int(request.GET.get('adults', 1) or request.session.get('adults', 1))
    children = int(request.GET.get('children', 0) or request.session.get('children', 0))
    rooms = int(request.GET.get('rooms', 1) or request.session.get('rooms', 1))

    request.session['checkin_date'] = checkin_date
    request.session['checkout_date'] = checkout_date
    request.session['adults'] = adults
    request.session['children'] = children
    request.session['rooms'] = rooms
    context = {
        'hotel': hotel,
        'hotel_rooms': hotel_rooms,
        'room_form': room_form,
        'checkin_date': checkin_date,
        'checkout_date': checkout_date,
        'adults': adults,
        'children': children,
        'rooms': rooms,

    }

    return render(request, 'hotel_detail.html', context)


def hotels(request):
    checkin_date = request.GET.get('checkin_date') or request.session.get('checkin_date', '')
    checkout_date = request.GET.get('checkout_date') or request.session.get('checkout_date', '')
    adults = int(request.GET.get('adults', 1) or request.session.get('adults', 1))
    children = int(request.GET.get('children', 0) or request.session.get('children', 0))
    rooms = int(request.GET.get('rooms', 1) or request.session.get('rooms', 1))

    request.session['checkin_date'] = checkin_date
    request.session['checkout_date'] = checkout_date
    request.session['adults'] = adults
    request.session['children'] = children
    request.session['rooms'] = rooms

    def calculate_days(checkin, checkout):
        if checkout and checkin:
            checkin_date = datetime.strptime(checkin, '%Y-%m-%d').date()
            checkout_date = datetime.strptime(checkout, '%Y-%m-%d').date()
            return (checkout_date - checkin_date).days
        else:
            return 1

    num_days = calculate_days(checkin_date, checkout_date)

    free_wifi = request.GET.get('free_wifi')
    fitness_center = request.GET.get('fitness_center')
    breakfast = request.GET.get('breakfast')
    swimming_pool = request.GET.get('swimming_pool')

    request.session['free_wifi'] = free_wifi
    request.session['fitness_center'] = fitness_center
    request.session['breakfast'] = breakfast
    request.session['swimming_pool'] = swimming_pool
    boolean_filters = {}
    if free_wifi:
        boolean_filters['free_wifi'] = True
    if fitness_center:
        boolean_filters['fitness_center'] = True
    if breakfast:
        boolean_filters['breakfast'] = True
    if swimming_pool:
        boolean_filters['swimming_pool'] = True

    hotels_matching_features = Hotel.objects.filter(
        Q(room_types__capacity=adults + children) |
        Q(room_types__capacity__gte=adults + children, room_types__price__lte=rooms),
        **boolean_filters
    ).distinct()
    room_type_names = {}
    for hotel in hotels_matching_features:
        matching_room_type = hotel.room_types.filter(capacity=adults + children).first()
        if matching_room_type:
            total_cost = num_days * matching_room_type.price * adults
            hotel.total_cost = total_cost
            room_type_names[hotel.id] = matching_room_type.name
            hotel.save()

    context = {
        'hotels': hotels_matching_features,
        'checkin_date': checkin_date,
        'checkout_date': checkout_date,
        'adults': adults,
        'children': children,
        'rooms': rooms,
        'days': num_days,
        'num_days': num_days,
        'room_type_names': room_type_names,

    }

    return render(request, 'hotels.html', context)


def reservation_success(request):
    return render(request, 'reservation_success.html')


def user_register(request):
    if request.method == "POST":
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            return redirect("login")
        messages.error(request, "Unsuccessful registration. Invalid information.")
    form = UserForm()
    return render(request, "register.html", context={"register_form": form})


def user_login(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)

                return redirect("homepage")
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    form = AuthenticationForm()
    return render(request, "login.html", context={"login_form": form})


def user_logout(request):
    logout(request)
    # messages.info(request, "You have successfully logged out.")
    return redirect("homepage")


class ReserveRoomView(View):
    template_name = 'hotel_detail.html'

    def get(self, request, hotel_id, *args, **kwargs):
        hotel = Hotel.objects.get(pk=hotel_id)
        room_types = RoomType.objects.filter(hotel=hotel)
        form = RoomReservationForm(room_types=room_types)
        context = {
            'hotel': hotel,
            'room_types': room_types,
            'form': form,
        }
        return render(request, self.template_name, context)

    def post(self, request, hotel_id, *args, **kwargs):

        hotel = Hotel.objects.get(pk=hotel_id)
        room_types = RoomType.objects.filter(hotel=hotel)
        form = RoomReservationForm(room_types=room_types, data=request.POST)
        checkin_date = request.session.get('checkin_date')
        checkout_date = request.session.get('checkout_date')
        reservation_successful = False
        total_cost = 0

        def calculate_days(checkin_date, checkout_date):
            checkin = datetime.strptime(checkin_date, '%Y-%m-%d').date()
            checkout = datetime.strptime(checkout_date, '%Y-%m-%d').date()
            return (checkout - checkin).days

        num_days = calculate_days(checkin_date, checkout_date)
        if form.is_valid():
            guest_name = form.cleaned_data['guest_name']
            guest_phone = form.cleaned_data['guest_phone']

            for room_type in room_types:
                quantity = form.cleaned_data.get(f'quantity_{room_type.id}', 0)

                try:
                    room_instances = HotelRoom.objects.filter(room_type=room_type)

                    if room_instances.exists():
                        # Choose the first instance (you may need to refine this based on your business logic)
                        availability = room_instances.first()

                        if int(quantity) > 0 and int(quantity) <= availability.available_rooms:
                            availability.available_rooms -= int(quantity)
                            availability.save()

                            room_type_cost = (room_type.price * int(quantity)) * num_days
                            total_cost += room_type_cost


                            reservation = RoomReservation.objects.create(
                                room_type=room_type,
                                quantity=quantity,
                                guest_name=guest_name,
                                guest_phone=guest_phone,
                                guest_email=request.user.email,
                                user=request.user,
                                checkin_date=checkin_date,
                                checkout_date=checkout_date,
                                hotel=hotel,
                                num_days=num_days,
                                cost=room_type_cost
                            )
                            reservation_successful = True

                except ObjectDoesNotExist:

                    pass

            if reservation_successful:
                user_reservations = RoomReservation.objects.filter(user=request.user)

                messages.success(request, f"Reservation successful! Total cost: ${total_cost}")
                subject = 'HotelGo - Reservation Confirmation'
                message = f'Thank you for your reservation! \n\n Your reservations:\n '
                for reservation in user_reservations:
                    message += f'Reservation ID: {reservation.id}\n'
                    message += f'Hotel Name: {reservation.hotel.name}\n'
                    message += f'Hotel Name: {reservation.hotel.location}\n'
                    message += f'Check-in Date: {reservation.checkin_date}\n'
                    message += f'Check-out Date: {reservation.checkout_date}\n'
                    message += f'Room Type: {reservation.room_type.name}\n'
                    message += f'No.of Rooms: {reservation.quantity}\n'
                    message += f'Price: ${reservation.cost}\n\n'
                from_email = settings.DEFAULT_FROM_EMAIL
                to_email = [request.user.email]

                send_mail(subject, message, from_email, to_email, fail_silently=False)

                return redirect('reservation_success')

        context = {
            'hotel': hotel,
            'room_types': room_types,
            'form': form,
        }
        return render(request, self.template_name, context)


def my_reservation(request):
    if request.user.is_superuser:
        reservations = RoomReservation.objects.all()
        template_name = 'admin_reservations.html'
    else:
        reservations = RoomReservation.objects.filter(user=request.user)
        template_name = 'my_reservations.html'

    context = {'reservations': reservations}
    return render(request, template_name, context)


def hotel_upload(request):
    if request.method == 'POST':
        hotel_form = HotelForm(request.POST, request.FILES)
        room_type_form = RoomTypeForm(request.POST)

        if hotel_form.is_valid():
            hotel = hotel_form.save(commit=False)

            hotel.save()

            return redirect('hotels')

    else:
        hotel_form = HotelForm()
        room_type_form = RoomTypeForm()

    return render(request, 'hotel_upload.html', {'hotel_form': hotel_form, 'room_type_form': room_type_form})


def add_room_type(request):
    if request.method == 'POST':
        room_type_form = RoomTypeForm(request.POST)
        if room_type_form.is_valid():
            room_type_form.save()
            return redirect('hotel_upload')
    return redirect('hotel_upload')


def update_available_rooms(request, hotel_id):
    hotel = get_object_or_404(Hotel, pk=hotel_id)

    if request.method == 'POST':
        room_form = HotelRoomForm(request.POST)
        if room_form.is_valid():
            room_type = room_form.cleaned_data['room_type']
            available_rooms = room_form.cleaned_data['available_rooms']
            hotel_room, created = HotelRoom.objects.get_or_create(hotel=hotel, room_type=room_type)
            hotel_room.available_rooms = available_rooms
            hotel_room.save()

            return redirect('hotel_detail', hotel_id=hotel.id)
    else:
        return redirect('hotel_detail', hotel_id=hotel.id)


def manage_rooms(request, hotel_id):
    hotel = get_object_or_404(Hotel, pk=hotel_id)

    if request.method == 'POST':
        room_form = HotelRoomForm(request.POST)
        if room_form.is_valid():
            room = room_form.save(commit=False)
            room.hotel = hotel
            room.save()
            return redirect('hotel_detail', hotel_id=hotel.id)
    else:
        room_form = HotelRoomForm()

    return render(request, 'manage_rooms.html', {'hotel': hotel, 'room_form': room_form})


def edit_hotel(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)

    if request.method == 'POST':
        form = HotelForm(request.POST, request.FILES, instance=hotel)
        if form.is_valid():
            form.save()
            return redirect('hotel_detail', hotel_id=hotel.id)
    else:
        form = HotelForm(instance=hotel)

    return render(request, 'edit_hotel.html', {'form': form, 'hotel': hotel})


def delete_hotel(request, hotel_id):
    hotel = get_object_or_404(Hotel, id=hotel_id)

    if request.method == 'POST':
        hotel.delete()
        return redirect('homepage')

    return render(request, 'delete_hotel.html', {'hotel': hotel})


def reservation_list(request, hotel_id):
    hotel = Hotel.objects.get(pk=hotel_id)

    reservations = RoomReservation.objects.filter(hotel=hotel)

    return render(request, 'reservation_list.html', {'hotel': hotel, 'reservations': reservations})
