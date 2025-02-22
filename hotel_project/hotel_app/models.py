# django data models that will be used to create & maintain the database tables
# to store data entered by the user
from datetime import timedelta
import logging
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models

# Configure logging
logger = logging.getLogger(__name__)

class Guest(models.Model):
    """
    Model representing a hotel guest with their personal and contact information.

    This model stores comprehensive guest details including name, contact information,
    and full address for booking and communication purposes.
    """
    guest_id = models.AutoField(primary_key=True)  # Unique identifier for each guest
    title = models.CharField(max_length=10)  # Guest's title (Mr., Mrs., Ms., etc.)
    first_name = models.CharField(max_length=50)  # Guest's first name
    last_name = models.CharField(max_length=50)  # Guest's last name
    phone_number = models.CharField(max_length=11)  # Contact phone number
    email = models.EmailField(max_length=320)  # Contact email address
    address_line1 = models.CharField(max_length=80)  # Primary address line
    address_line2 = models.CharField(max_length=80, blank=True, null=True)  # Secondary address line (optional)
    city = models.CharField(max_length=80)  # City of residence
    county = models.CharField(max_length=80)  # County/state/region
    postcode = models.CharField(max_length=8)  # Postal/ZIP code

    def __str__(self):
        """
        Return a string representation of the guest.

        Returns:
            str: A string in the format 'ID:{id}: Full name:{title first_name last_name}'
                e.g., 'ID:123: Full name:Mr John Smith'
        """
        guest_str = f"ID:{self.guest_id}: Full name:{self.title} {self.first_name} {self.last_name}"
        logger.info(f"Guest __str__ called: {guest_str}")
        return guest_str

    @property
    def display_name(self):
        """
        Return a shorter formatted name for display purposes.

        Returns:
            str: A string in the format '{title} {first_initial}. {last_name}'
                e.g., 'Mr J. Smith'
        """
        display_name = f"{self.title} {self.first_name[0]}. {self.last_name}"
        logger.info(f"Guest display_name property called: {display_name}")
        return display_name


class RoomType(models.Model):
    """
    Model representing different types of hotel rooms and their characteristics.

    This model defines various room categories with their amenities, pricing,
    and capacity information. Each room type has a unique code and specific features
    that distinguish it from other types.
    """
    room_type_code = models.CharField(
        max_length=3,
        validators=[
            MinLengthValidator(1),
            RegexValidator(r'^[A-Z]{1,3}$', message="The room type code must be between 1 and 3 uppercase letters"),
        ],
        unique=True,
        primary_key=True,
        help_text="Unique 1-3 letter code for the room type (e.g., 'STD' for Standard)"
    )
    room_type_name = models.CharField(
        max_length=25,
        help_text="Descriptive name for the room type"
    )
    price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Nightly rate for this room type"
    )
    deluxe = models.BooleanField(
        help_text="Indicates if this is a deluxe category room"
    )
    bath = models.BooleanField(
        help_text="Indicates if the room has a bathtub"
    )
    separate_shower = models.BooleanField(
        help_text="Indicates if the room has a separate shower unit"
    )
    maximum_guests = models.PositiveSmallIntegerField(
        help_text="Maximum number of guests allowed in this room type"
    )

    def __str__(self):
        room_type_str = self.room_type_name
        logger.info(f"RoomType __str__ called: {room_type_str}")
        return room_type_str


class Room(models.Model):
    """
    Model representing individual hotel rooms.

    Each room has a unique room number and is associated with a specific room type
    that defines its characteristics and pricing. This model creates the link between
    physical rooms and their type specifications.
    """
    room_number = models.IntegerField(
        primary_key=True,
        unique=True,
        help_text="Unique identifier for the room (e.g., 101, 102, etc.)"
    )
    room_type = models.ForeignKey(
        RoomType,
        null=True,
        on_delete=models.SET_NULL,
        related_name="rooms",
        help_text="The type/category of this room, determining its features and price"
    )

    def __str__(self):
        room_str = f"{self.room_number}"
        logger.info(f"Room __str__ called: {room_str}")
        return room_str


class Reservation(models.Model):
    """
    Model representing hotel room reservations.

    This model tracks all aspects of a room booking including guest information,
    room details, dates, payment status, and booking status. It manages the complete
    lifecycle of a reservation from initial booking through check-out.
    """
    STATUS_CHOICES = [
        ("RE", "Reserved"),  # Initial reservation status
        ("IN", "Checked In"),  # Guest has arrived and checked in
        ("OT", "Checked Out"),  # Guest has completed their stay
    ]

    reservation_id = models.AutoField(
        primary_key=True,
        help_text="Unique identifier for the reservation"
    )
    guest = models.ForeignKey(
        Guest,
        null=True,
        on_delete=models.SET_NULL,
        related_name="reservations",
        help_text="Guest making the reservation"
    )
    room_number = models.ForeignKey(
        Room,
        null=True,
        on_delete=models.SET_NULL,
        related_name="reservations",
        help_text="Room assigned to this reservation"
    )
    reservation_date_time = models.DateTimeField(
        help_text="Date and time when the reservation was made"
    )
    price = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Total price for the entire stay"
    )
    amount_paid = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        help_text="Amount already paid by the guest"
    )
    number_of_guests = models.PositiveSmallIntegerField(
        help_text="Number of guests staying in the room"
    )
    start_of_stay = models.DateField(
        help_text="Check-in date"
    )
    length_of_stay = models.PositiveSmallIntegerField(
        help_text="Number of nights booked"
    )
    status_code = models.CharField(
        max_length=2,
        choices=STATUS_CHOICES,
        help_text="Current status of the reservation"
    )
    notes = models.TextField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Additional notes or special requests for the reservation"
    )

    @property
    def end_date(self):
        """
        Calculate and return the check-out date.

        Returns:
            datetime.date: The date when the guest is expected to check out,
                         calculated as start_of_stay + length_of_stay days
        """
        end_date = self.start_of_stay + timedelta(days=self.length_of_stay)
        logger.info(f"Reservation end_date property called: {end_date}")
        return end_date

    def __str__(self):
        """
        Return a string representation of the reservation.

        Returns:
            str: A string in the format 'Reservation {id} - {status}'
                e.g., 'Reservation 123 - IN' for a checked-in reservation
        """
        reservation_str = f"Reservation {self.reservation_id} - {self.status_code}"
        logger.info(f"Reservation __str__ called: {reservation_str}")
        return reservation_str
