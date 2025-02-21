"""
Hotel Management System Views

This module contains all the view functions for the hotel management application.
It handles:
- User authentication (login/logout)
- Guest management (CRUD operations)
- Room management (CRUD operations)
- Room type management (CRUD operations)
- Reservation management (booking, check-in, check-out)
- Room availability checking

Each view function is responsible for:
- Processing HTTP requests (GET/POST)
- Form handling and validation
- Data preparation for templates
- Business logic implementation
- Navigation flow control
"""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from datetime import datetime, date, timedelta
from . models import Guest, Reservation, Room, RoomType
from . filters import AvailableRoomFilter, GuestFilter, ReservationFilter
from . forms import LoginForm, GuestForm, ReservationForm, RoomForm, RoomTypeForm
import logging

# Configure logging to write INFO level messages or higher to the terminal
# This provides detailed operation tracking for debugging and monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Authentication Views

def login_view(request):
    """
    Handle user authentication and login.

    This view manages the login process by:
    1. Checking if user is already authenticated
    2. Processing login form submission
    3. Authenticating credentials
    4. Creating user session on successful login

    Args:
        request: HttpRequest object containing user data and form submission

    Returns:
        HttpResponse: Renders login form or redirects to home page on success
    """
    if request.user.is_authenticated:
        return redirect('home')  # User already logged in, redirect to home page

    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')  # Successful login, redirect to home page
    else:
        form = LoginForm()  # Create empty form for GET request

    return render(request, "login.html", {"form": form})


@login_required
def logout_view(request):
    """
    Handle user logout.

    This view terminates the user's session and redirects to the login page.
    Protected by @login_required to ensure only authenticated users can logout.

    Args:
        request: HttpRequest object containing user session data

    Returns:
        HttpResponse: Redirects to login page after logging out
    """
    logout(request)
    return redirect('login')

# Home Page View

@login_required
def home_view(request):
    """
    Display the main dashboard/home page of the hotel management system.

    This view serves as the landing page after login, showing different options
    based on user permissions. It checks if the user has manager privileges
    to potentially show additional management features.

    Args:
        request: HttpRequest object containing user session and permissions data

    Returns:
        HttpResponse: Renders the home page template

    Notes:
        - Protected by @login_required decorator
        - Checks for 'Manager' group membership for additional features
    """
    # Check if user belongs to the 'Manager' group for permission-based content
    is_manager = request.user.groups.filter(name='Manager').exists()

    return render(request, 'home.html')

# Guest Management Views

@login_required
def guest_create_view(request):
    """
    Create a new guest record in the system.

    This view handles both the display and processing of the guest registration form.
    It supports two modes of operation:
    - Standard mode: Returns to guest list after creation
    - Selection mode: Returns to guest selection page (used during reservation)

    Args:
        request: HttpRequest object containing form data and mode parameter

    Returns:
        HttpResponse: Renders guest form or redirects based on mode
    """
    mode = request.GET.get('mode', 'list')  # Get operation mode from query param

    if request.method == 'POST':
        form = GuestForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirect based on operation mode
            if mode == 'selection':
                return redirect('guest_selection')
            else:
                return redirect('guest_list')
    else:
        form = GuestForm()

    return render(request, 'guest_form.html', {
        'form': form,
        'title': 'Guest Registration'
    })


@login_required
def guest_list_view(request):
    """
    Display a filterable list of all guests.

    This view shows all registered guests and provides filtering capabilities
    through the GuestFilter class. Users can search and filter guests based
    on various criteria.

    Args:
        request: HttpRequest object containing filter parameters

    Returns:
        HttpResponse: Renders guest list with filter form
    """
    guests = Guest.objects.all()
    guest_filter = GuestFilter(request.GET, queryset=guests)
    return render(request, 'guest_list.html', {'filter': guest_filter})


@login_required
def guest_update_view(request, guest_id):
    """
    Update an existing guest's information.

    This view handles the editing of guest details, including validation
    and saving of the updated information.

    Args:
        request: HttpRequest object containing form data
        guest_id: Primary key of the guest to update

    Returns:
        HttpResponse: Renders edit form or redirects to list on success

    Raises:
        Guest.DoesNotExist: If guest_id is not found
    """
    guest = Guest.objects.get(guest_id=guest_id)
    if request.method == "POST":
        form = GuestForm(request.POST, instance=guest)
        if form.is_valid():
            form.save()
            return redirect('guest_list')
    else:
        form = GuestForm(instance=guest)

    return render(request, 'guest_form.html', {
        'form': form,
        'title': 'Edit Guest Details'
    })


@login_required
def guest_delete_view(request, guest_id):
    """
    Delete a guest record from the system.

    This view handles the confirmation and deletion of guest records.
    It requires a POST request for actual deletion to prevent accidental
    deletions through GET requests.

    Args:
        request: HttpRequest object
        guest_id: Primary key of the guest to delete

    Returns:
        HttpResponse: Renders confirmation page or redirects after deletion

    Raises:
        Guest.DoesNotExist: If guest_id is not found
    """
    guest = Guest.objects.get(guest_id=guest_id)
    if request.method == 'POST':
        guest.delete()
        return redirect('guest_list')
    return render(request, 'guest_confirm_delete.html', {'guest': guest})

# Room Availability Management Views

@login_required
def available_rooms_list_view(request):
    """
    Display a list of available rooms based on search criteria.

    This view handles the search for available rooms based on:
    - Check-in date
    - Length of stay
    - Room type preferences

    The view maintains search criteria in the session for user convenience
    and applies default values when criteria are not specified.

    Args:
        request: HttpRequest object containing search parameters

    Returns:
        HttpResponse: Renders available rooms list with filter form
    """
    # Process start date parameter with session fallback
    start_date = request.GET.get('start_date')
    if not start_date:
        start_date = request.session.get(
            'available_rooms_default_start_date',
            timezone.now().date().strftime('%Y-%m-%d')  # Default to today
        )

    # Process length of stay parameter with session fallback
    length_of_stay = request.GET.get('length_of_stay')
    if not length_of_stay:
        length_of_stay = request.session.get(
            'available_rooms_default_length_of_stay',
            1  # Default to 1 night
        )

    # Process room type parameter with session fallback
    room_type = request.GET.get('room_type')
    if not room_type:
        room_type = request.session.get(
            'available_rooms_default_room_type',
            ''  # Default to all room types
        )

    # Persist search criteria in session for future use
    request.session['available_rooms_default_start_date'] = start_date
    request.session['available_rooms_default_length_of_stay'] = length_of_stay
    request.session['available_rooms_default_room_type'] = room_type

    # Apply filters to room queryset
    rooms = Room.objects.all()
    available_room_filter = AvailableRoomFilter(
        request.GET or {
            'start_date': start_date,
            'length_of_stay': length_of_stay,
            'room_type': room_type
        },
        queryset=rooms
    )

    return render(request, 'available_rooms_list.html', {
        'filter': available_room_filter
    })


@login_required
def available_rooms_reserve_view(request, room_number):
    """
    Initiate the room reservation process.

    This view stores the selected room and stay details in the session
    before redirecting to guest selection. It acts as a bridge between
    room selection and guest assignment.

    Args:
        request: HttpRequest object containing stay details
        room_number: The selected room's identifier

    Returns:
        HttpResponse: Redirects to guest selection page
    """
    # Store reservation details in session
    request.session['selected_room_number'] = room_number
    request.session['selected_start_date'] = request.GET.get('start_date')
    request.session['selected_length_of_stay'] = request.GET.get('length_of_stay')

    return redirect('available_rooms_guest_selection')


@login_required
def available_rooms_guest_selection_view(request):
    """
    Display guest selection interface for room reservation.

    This view shows a filterable list of guests to associate with the
    selected room reservation. It retrieves reservation details from
    the session and presents them alongside the guest selection interface.

    Args:
        request: HttpRequest object

    Returns:
        HttpResponse: Renders guest selection page with reservation details

    Notes:
        Requires the following session data:
        - selected_room_number
        - selected_start_date
        - selected_length_of_stay
    """
    # Retrieve reservation details from session
    room_number = request.session.get('selected_room_number')
    start_date = request.session.get('selected_start_date')
    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    length_of_stay = request.session.get('selected_length_of_stay')

    # Prepare guest selection interface
    guests = Guest.objects.all()
    guest_filter = GuestFilter(request.GET, queryset=guests)

    return render(request, 'guest_selection.html', {
        'filter': guest_filter,
        'room_number': room_number,
        'start_date': start_date_obj,
        'length_of_stay': length_of_stay,
    })

# Reservation Management Views

@login_required
def reservation_create_view(request, guest_id):
    """
    Create a new reservation for a specific guest.

    This view handles the creation of a new reservation by:
    1. Retrieving guest and room details from session/database
    2. Calculating stay duration and total price
    3. Preparing and processing the reservation form
    4. Handling form submission and validation

    Args:
        request: HttpRequest object containing session data
        guest_id: ID of the guest making the reservation

    Returns:
        HttpResponse: Renders reservation form or redirects to confirmation

    Raises:
        Guest.DoesNotExist: If guest_id is not found
        Room.DoesNotExist: If room_number from session is not found
    """
    logger.info(f"reservation_create_view called guest_id: {guest_id}")
    request.session['selected_guest_id'] = guest_id

    # Gather reservation details
    guest = Guest.objects.get(guest_id=guest_id)
    room_number = request.session.get('selected_room_number', -1)
    room = Room.objects.get(room_number=room_number)

    # Process dates and calculate price
    start_date = request.session.get('selected_start_date',
                                   date.today().strftime('%Y-%m-%d'))
    start_of_reservation = datetime.strptime(start_date, "%Y-%m-%d").date()
    length_of_stay = request.session.get('selected_length_of_stay', 1)
    price_for_stay = room.room_type.price * int(length_of_stay)

    # Log reservation details for debugging
    logger.info(f"Selected guest = Guest Id: {guest_id}, Name: {guest.display_name}")
    logger.info(f"Selected room = {room.room_number}")
    logger.info(f"Selected start_date = {start_of_reservation}")
    logger.info(f"Price per night: {room.room_type.price}")
    logger.info(f"Length of stay: {length_of_stay}")
    logger.info(f"Price for stay: {price_for_stay}")

    # Prepare initial form data
    initial_data = {
        'room_number': room,
        'start_of_stay': start_of_reservation,
        'guest': guest,
        'number_of_guests': 1,
        'length_of_stay': length_of_stay,
        'status_code': "RE",
        'reservation_date_time': datetime.now(),
        'price': price_for_stay,
        'amount_paid': 0,
    }

    if request.method == 'POST':
        logger.info(f"Post message = {request.POST}")
        form = ReservationForm(request.POST, initial=initial_data)
        if form.is_valid():
            reservation = form.save()
            return redirect('reservation_confirmed',
                          reservation_id=reservation.reservation_id)
        logger.info("Reservation form validation failed")
    else:
        form = ReservationForm(initial=initial_data)

    context = {
        'form': form,
        'title': 'Create Reservation',
        'save_button_text': 'Create Reservation',
    }

    return render(request, 'reservation_form.html', context)


@login_required
def reservation_confirmed_view(request, reservation_id):
    """
    Display confirmation page for a successful reservation.

    Args:
        request: HttpRequest object
        reservation_id: ID of the confirmed reservation

    Returns:
        HttpResponse: Renders confirmation page with reservation details

    Raises:
        Reservation.DoesNotExist: If reservation_id is not found
    """
    reservation = Reservation.objects.get(reservation_id=reservation_id)
    return render(request, 'reservation_confirmed.html',
                 {'reservation': reservation})


@login_required
def reservation_list_view(request):
    """
    Display a filterable list of all reservations.

    This view provides a comprehensive list of reservations with filtering
    capabilities based on:
    - Date range (start and end dates)
    - Guest's last name
    - Room number

    The view maintains filter preferences in the session for user convenience
    and applies default values when filters are not specified.

    Args:
        request: HttpRequest object containing filter parameters

    Returns:
        HttpResponse: Renders reservation list with filter form
    """
    logger.info(f"Reservation List View - GET request = {request.GET}")

    # Process start date with session fallback
    start_date = request.GET.get('start_date')
    if start_date is None:
        start_date = request.session.get(
            'reservations_default_start_date',
            timezone.now().date().strftime('%Y-%m-%d')  # Default to today
        )

    # Process end date with session fallback
    end_date = request.GET.get('end_date')
    if end_date is None:
        today_plus_two_weeks = datetime.now() + timedelta(weeks=2)
        end_date = request.session.get(
            'reservations_default_end_date',
            today_plus_two_weeks.date().strftime('%Y-%m-%d')  # Default to 2 weeks ahead
        )

    # Process guest name filter with session fallback
    last_name = request.GET.get('last_name')
    if last_name is None:
        last_name = request.session.get('reservations_default_last_name', '')

    # Process room number filter with session fallback
    room_number = request.GET.get('room_number')
    if room_number is None:
        room_number = request.session.get('reservations_default_room_number', '')

    # Persist filter preferences in session
    request.session.update({
        'reservations_default_start_date': start_date,
        'reservations_default_end_date': end_date,
        'reservations_default_last_name': last_name,
        'reservations_default_room_number': room_number
    })

    # Apply filters to reservation queryset
    reservations = Reservation.objects.all()
    reservation_filter = ReservationFilter(
        request.GET or {
            'start_date': start_date,
            'end_date': end_date,
            'last_name': last_name,
            'room_number': room_number
        },
        queryset=reservations
    )

    return render(request, 'reservation_list.html',
                 {'filter': reservation_filter})


@login_required
def reservation_update_view(request, reservation_id):
    """
    Update an existing reservation or change its status.

    This view handles multiple operations on a reservation:
    1. General reservation details update
    2. Guest check-in process
    3. Guest check-out process

    The operation mode is determined by the 'status_code' parameter:
    - No status_code: Regular reservation update
    - status_code="IN": Check-in process
    - status_code="OT": Check-out process

    Args:
        request: HttpRequest object containing form data and status code
        reservation_id: ID of the reservation to update

    Returns:
        HttpResponse: Renders update form or redirects to list on success

    Raises:
        Reservation.DoesNotExist: If reservation_id is not found
    """
    # Retrieve reservation and related objects
    reservation = Reservation.objects.get(reservation_id=reservation_id)
    guest = reservation.guest
    room = reservation.room_number

    # Determine operation mode from status code
    status_code = request.GET.get('status_code')

    if status_code == "IN":
        # Check-in mode: Update status and set form labels
        reservation.status_code = "IN"
        title = 'Check-in a Reservation'
        save_button_text = 'Save Check-in'
    elif status_code == "OT":
        # Check-out mode: Update status and set form labels
        reservation.status_code = "OT"
        title = 'Check-out a Reservation'
        save_button_text = 'Save Check-out'
    else:
        # Regular update mode
        title = 'Edit a Reservation'
        save_button_text = 'Update Reservation'

    if request.method == 'POST':
        # Process form submission
        logger.info(f"Processing reservation update: {request.POST}")
        form = ReservationForm(request.POST, instance=reservation)
        if form.is_valid():
            form.save()
            return redirect('reservation_list')
        else:
            logger.info("Reservation update form validation failed")
    else:
        # Display form for GET request
        form = ReservationForm(instance=reservation)

    context = {
        'form': form,
        'title': title,
        'save_button_text': save_button_text,
    }

    return render(request, 'reservation_form.html', context)


@login_required
def reservation_delete_view(request, reservation_id):
    """
    Delete an existing reservation.

    This view handles the deletion of reservations with a confirmation step:
    1. GET request: Shows confirmation page
    2. POST request: Performs the actual deletion

    Args:
        request: HttpRequest object
        reservation_id: ID of the reservation to delete

    Returns:
        HttpResponse: Renders confirmation page or redirects after deletion

    Raises:
        Reservation.DoesNotExist: If reservation_id is not found
    """
    reservation = Reservation.objects.get(reservation_id=reservation_id)

    if request.method == 'POST':
        # Actual deletion on POST request
        reservation.delete()
        return redirect('reservation_list')

    # Show confirmation page on GET request
    return render(request, 'reservation_confirm_delete.html',
                 {'reservation': reservation})


# Room Management Views

@login_required
@user_passes_test(lambda user: user.groups.filter(name='Manager').exists())
def room_create_view(request):
    """
    Create a new room in the hotel.

    This view handles the creation of new room records. It is restricted
    to users in the 'Manager' group for security purposes.

    Args:
        request: HttpRequest object containing form data

    Returns:
        HttpResponse: Renders room form or redirects to list on success

    Notes:
        - Requires login
        - Requires 'Manager' group membership
    """
    if request.method == 'POST':
        form = RoomForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('room_list')
    else:
        form = RoomForm()

    return render(request, 'room_form.html', {'form': form})


@login_required
@user_passes_test(lambda user: user.groups.filter(name='Manager').exists())
def room_list_view(request):
    """
    Display a list of all rooms in the hotel.

    This view shows all rooms and their current configurations.
    Access is restricted to managers only.

    Args:
        request: HttpRequest object

    Returns:
        HttpResponse: Renders room list page

    Notes:
        - Requires login
        - Requires 'Manager' group membership
    """
    rooms = Room.objects.all()
    return render(request, 'room_list.html', {'rooms': rooms})


@login_required
@user_passes_test(lambda user: user.groups.filter(name='Manager').exists())
def room_update_view(request, room_number):
    """
    Update an existing room's details.

    This view handles modifications to room configurations, including:
    - Room type assignment
    - Room status updates
    - Other room-specific settings

    Args:
        request: HttpRequest object containing form data
        room_number: Identifier of the room to update

    Returns:
        HttpResponse: Renders update form or redirects to list on success

    Raises:
        Room.DoesNotExist: If room_number is not found

    Notes:
        - Requires login
        - Requires 'Manager' group membership
    """
    room = Room.objects.get(room_number=room_number)
    if request.method == "POST":
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            return redirect('room_list')
    else:
        form = RoomForm(instance=room)

    return render(request, 'room_form.html', {'form': form})


@login_required
@user_passes_test(lambda user: user.groups.filter(name='Manager').exists())
def room_delete_view(request, room_number):
    """
    Delete a room from the hotel system.

    This view handles the removal of rooms with a confirmation step:
    1. GET request: Shows confirmation page
    2. POST request: Performs the actual deletion

    Args:
        request: HttpRequest object
        room_number: Identifier of the room to delete

    Returns:
        HttpResponse: Renders confirmation page or redirects after deletion

    Raises:
        Room.DoesNotExist: If room_number is not found

    Notes:
        - Requires login
        - Requires 'Manager' group membership
        - Should be used with caution as it permanently removes the room
    """
    room = Room.objects.get(room_number=room_number)
    if request.method == 'POST':
        room.delete()
        return redirect('room_list')
    return render(request, 'room_confirm_delete.html', {'room': room})

# Room Type Management Views

@login_required
@user_passes_test(lambda user: user.groups.filter(name='Manager').exists())
def room_type_create_view(request):
    """
    Create a new room type configuration.

    This view handles the creation of new room type categories, including:
    - Basic details (code, name)
    - Pricing information
    - Amenities and features
    - Capacity settings

    Args:
        request: HttpRequest object containing form data

    Returns:
        HttpResponse: Renders room type form or redirects to list on success

    Notes:
        - Requires login
        - Requires 'Manager' group membership
        - Validates room type code format
        - Logs form validation errors for debugging
    """
    if request.method == 'POST':
        form = RoomTypeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('room_type_list')
        else:
            logger.error("Room type creation failed")
            logger.error(f"Form errors: {form.errors}")
    else:
        form = RoomTypeForm()

    return render(request, 'room_type_form.html', {'form': form})


@login_required
@user_passes_test(lambda user: user.groups.filter(name='Manager').exists())
def room_type_list_view(request):
    """
    Display a list of all room types.

    This view shows all available room type configurations, including:
    - Type codes and names
    - Current pricing
    - Available amenities
    - Maximum capacity

    Args:
        request: HttpRequest object

    Returns:
        HttpResponse: Renders room type list page

    Notes:
        - Requires login
        - Requires 'Manager' group membership
        - Used for room type management and reference
    """
    room_types = RoomType.objects.all()
    return render(request, 'room_type_list.html',
                 {'room_types': room_types})

@login_required
@user_passes_test(lambda user: user.groups.filter(name='Manager').exists())
def room_type_update_view(request, room_type_code):
    """
    Update an existing room type configuration.

    This view handles modifications to room type settings, including:
    - Basic information updates
    - Price adjustments
    - Amenity changes
    - Capacity modifications

    Args:
        request: HttpRequest object containing form data
        room_type_code: Unique code of the room type to update

    Returns:
        HttpResponse: Renders update form or redirects to list on success

    Raises:
        RoomType.DoesNotExist: If room_type_code is not found

    Notes:
        - Requires login
        - Requires 'Manager' group membership
        - Changes affect all rooms of this type
    """
    room_type = RoomType.objects.get(room_type_code=room_type_code)
    if request.method == "POST":
        form = RoomTypeForm(request.POST, instance=room_type)
        if form.is_valid():
            form.save()
            return redirect('room_type_list')
    else:
        form = RoomTypeForm(instance=room_type)

    return render(request, 'room_type_form.html', {'form': form})


@login_required
@user_passes_test(lambda user: user.groups.filter(name='Manager').exists())
def room_type_delete_view(request, room_type_code):
    """
    Delete a room type from the system.

    This view handles the removal of room types with a confirmation step:
    1. GET request: Shows confirmation page
    2. POST request: Performs the actual deletion

    Args:
        request: HttpRequest object
        room_type_code: Unique code of the room type to delete

    Returns:
        HttpResponse: Renders confirmation page or redirects after deletion

    Raises:
        RoomType.DoesNotExist: If room_type_code is not found

    Notes:
        - Requires login
        - Requires 'Manager' group membership
        - Should be used with caution as it affects all rooms of this type
        - Consider impact on existing reservations before deletion
    """
    room_type = RoomType.objects.get(room_type_code=room_type_code)
    if request.method == 'POST':
        room_type.delete()
        return redirect('room_type_list')
    return render(request, 'room_type_confirm_delete.html',
                 {'room_type': room_type})
