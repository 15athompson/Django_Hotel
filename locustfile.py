from locust import HttpUser, task, between
import json
import random
from datetime import datetime, timedelta

class HotelUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login at the start of each user simulation"""
        self.client.headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        self.login()
        self.guest_id = None
        self.room_number = None
        self.reservation_id = None
        self.room_type_code = None
    
    def login(self):
        """Simulate user login with proper CSRF handling"""
        # Get the login page first to get the CSRF token
        response = self.client.get("/login/")
        if response.status_code == 200:
            # Extract CSRF token from response cookies
            csrf_token = response.cookies.get('csrftoken')
            if csrf_token:
                # Set CSRF token in headers and cookies
                self.client.headers['X-CSRFToken'] = csrf_token
                self.client.cookies['csrftoken'] = csrf_token
                
                # Perform login
                login_data = {
                    "username": "admin",  # Update with valid credentials
                    "password": "Pa$$1234",  # Update with valid credentials
                    "csrfmiddlewaretoken": csrf_token
                }
                return self.client.post("/login/", data=login_data)

    @task(2)
    def view_home(self):
        """View home page"""
        self.client.get("/")

    @task(3)
    def browse_available_rooms(self):
        """Browse available rooms"""
        self.client.get("/available-rooms/")

    # Guest Operations
    @task(2)
    def guest_operations(self):
        """Perform guest CRUD operations"""
        # List guests
        self.client.get("/guest/")

        # Create guest
        guest_data = {
            "title": "Mr",
            "first_name": f"Test{random.randint(1, 1000)}",
            "last_name": f"User{random.randint(1, 1000)}",
            "phone_number": f"07{random.randint(100000000, 999999999)}",
            "email": f"test{random.randint(1, 1000)}@example.com",
            "address_line1": f"{random.randint(1, 100)} Test Street",
            "city": "London",
            "county": "Greater London",
            "postcode": "SW1A 1AA"
        }

        # Set form content type for POST
        self.client.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        response = self.client.post("/guest/create/", data=guest_data)
        
        if response.status_code == 302:  # Successful redirect after creation
            # Get guest ID from redirect URL or list
            guest_list_response = self.client.get("/guest/list/")
            if guest_list_response.status_code == 200:
                # Here we would parse the response to get the latest guest ID
                self.guest_id = 1  # Placeholder - adjust based on actual response
                
                # Update guest
                if self.guest_id:
                    guest_data["first_name"] = f"Updated{random.randint(1, 1000)}"
                    self.client.post(f"/guest/{self.guest_id}/update/", data=guest_data)

    # Room Operations
    @task(2)
    def room_operations(self):
        """Perform room CRUD operations"""
        # List rooms
        self.client.get("/room/")

        # Create room
        room_data = {
            "room_number": str(random.randint(100, 999)),
            "room_type": "STD"  # Using standard room type code
        }

        self.client.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        response = self.client.post("/room/create/", data=room_data)
        
        if response.status_code == 302:  # Successful redirect after creation
            self.room_number = room_data["room_number"]
            
            # Update room
            if self.room_number:
                room_data["room_type"] = "DLX"  # Change to deluxe
                self.client.post(f"/room/{self.room_number}/update/", data=room_data)

    # Room Type Operations
    @task(1)
    def room_type_operations(self):
        """Perform room type CRUD operations"""
        # List room types
        self.client.get("/room-types/")

        # Create room type
        room_type_data = {
            "room_type_code": f"T{random.randint(1, 99)}",
            "room_type_name": f"Test Room Type {random.randint(1, 99)}",
            "price": str(random.randint(100, 500)),
            "deluxe": "true",
            "bath": "true",
            "separate_shower": "true",
            "maximum_guests": "2"
        }

        self.client.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        response = self.client.post("/room-types/create/", data=room_type_data)
        
        if response.status_code == 302:  # Successful redirect after creation
            self.room_type_code = room_type_data["room_type_code"]
            
            # Update room type
            if self.room_type_code:
                room_type_data["price"] = str(random.randint(100, 500))
                self.client.post(f"/room-types/{self.room_type_code}/update/", data=room_type_data)

    # Reservation Operations
    @task(3)
    def reservation_operations(self):
        """Perform reservation CRUD operations"""
        if self.guest_id and self.room_number:
            # Create reservation
            start_date = datetime.now().date()
            reservation_data = {
                "guest": str(self.guest_id),
                "room_number": str(self.room_number),
                "reservation_date_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "price": "200.00",
                "amount_paid": "200.00",
                "number_of_guests": "2",
                "start_of_stay": start_date.strftime("%Y-%m-%d"),
                "length_of_stay": "3",
                "status_code": "RE",
                "notes": "Test reservation"
            }
            
            self.client.headers['Content-Type'] = 'application/x-www-form-urlencoded'
            response = self.client.post("/reservation/create/", data=reservation_data)
            
            if response.status_code == 302:  # Successful redirect after creation
                # Get reservation ID from redirect URL or list
                reservation_list_response = self.client.get("/reservation/list/")
                if reservation_list_response.status_code == 200:
                    # Here we would parse the response to get the latest reservation ID
                    self.reservation_id = 1  # Placeholder - adjust based on actual response
                    
                    # Update reservation
                    if self.reservation_id:
                        reservation_data["length_of_stay"] = "4"
                        self.client.post(f"/reservation/{self.reservation_id}/update/", data=reservation_data)

    def on_stop(self):
        """Cleanup after user simulation"""
        # Delete created resources
        if self.reservation_id:
            self.client.post(f"/reservation/{self.reservation_id}/delete/")
        if self.guest_id:
            self.client.post(f"/guest/{self.guest_id}/delete/")
        if self.room_number:
            self.client.post(f"/room/{self.room_number}/delete/")
        if self.room_type_code:
            self.client.post(f"/room-types/{self.room_type_code}/delete/")
        self.client.get("/logout/")