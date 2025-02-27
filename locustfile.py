from locust import HttpUser, task, between
import json
import random
import logging
import time
from datetime import datetime, timedelta

class HotelUser(HttpUser):
    wait_time = between(3, 5)  # Increased wait time to reduce server load
    host = "http://localhost:8007"  # Set the base host URL
    connection_retries = 3  # Number of retries for connection issues

    def on_start(self):
        """Login at the start of each user simulation"""
        self.client.headers = {}  # Initialize empty headers
        self.csrf_token = None
        self.session_id = None
        if not self.login():
            logging.error("Failed to login, stopping user")
            self.stop()
        self.guest_id = None
        self.room_number = None
        self.room_type_code = None

    def update_csrf_token(self, response):
        """Update CSRF token and session from response"""
        csrf_token = response.cookies.get('csrftoken')
        if csrf_token:
            self.csrf_token = csrf_token
            self.client.headers['X-CSRFToken'] = csrf_token
            self.client.cookies['csrftoken'] = csrf_token

        # Update session ID if present
        session_id = response.cookies.get('sessionid')
        if session_id:
            self.session_id = session_id
            self.client.cookies['sessionid'] = session_id
    
    def login(self):
        """Simulate user login with proper CSRF handling"""
        for attempt in range(self.connection_retries):
            try:
                # Get the login page first to get the CSRF token
                with self.client.get("/login/", catch_response=True) as response:
                    if response.status_code == 200:
                        self.update_csrf_token(response)
                        if self.csrf_token:
                            # Set proper content type for form submission
                            self.client.headers['Content-Type'] = 'application/x-www-form-urlencoded'

                            # Perform login
                            login_data = {
                                "username": "admin",
                                "password": "admin123",
                                "csrfmiddlewaretoken": self.csrf_token
                            }

                            with self.client.post("/login/",
                                                data=login_data,
                                                allow_redirects=True,
                                                catch_response=True) as response:

                                if response.status_code in [200, 302]:  # Success or redirect
                                    self.update_csrf_token(response)
                                    return True
                                else:
                                    response.failure(f"Login failed with status code: {response.status_code}")

                        else:
                            response.failure("No CSRF token found in login page")

                    elif response.status_code == 503:
                        logging.warning(f"Server unavailable, attempt {attempt + 1} of {self.connection_retries}")
                        time.sleep(1)  # Wait before retry
                        continue
                    else:
                        response.failure(f"Failed to get login page: {response.status_code}")

            except ConnectionRefusedError as e:
                logging.warning(f"Connection refused, attempt {attempt + 1} of {self.connection_retries}")
                time.sleep(1)  # Wait before retry
                continue
            except Exception as e:
                logging.error(f"Login error: {str(e)}")
                return False

        return False  # All retries failed

    @task(2)
    def view_home(self):
        """View home page"""
        self.client.get("/")

    def handle_response(self, response, operation, retry_count=0):
        """Generic response handler with proper error logging"""
        try:
            if response.status_code >= 400:
                logging.error(f"{operation} failed with status {response.status_code}")
                logging.error(f"Response: {response.text[:200]}")  # Log first 200 chars of response

                # Update CSRF token if provided in error response
                self.update_csrf_token(response)

                # If session expired, try to login again
                if response.status_code == 403:
                    logging.warning("Session might have expired, attempting to login again")
                    if self.login() and retry_count < 1:
                        # Retry the operation once after successful login
                        return self.handle_response(response, operation, retry_count + 1)

            return response.status_code < 400
        except Exception as e:
            logging.error(f"Error handling response for {operation}: {str(e)}")
            return False

    @task(3)
    def browse_available_rooms(self):
        """Browse available rooms with proper parameters"""
        try:
            params = {
                'check_in': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'check_out': (datetime.now() + timedelta(days=3)).strftime('%Y-%m-%d'),
                'guests': '2'
            }
            with self.client.get("/available-rooms/",
                               params=params,
                               catch_response=True) as response:
                if not self.handle_response(response, "browse_available_rooms"):
                    response.failure("Failed to browse available rooms")
        except Exception as e:
            logging.error(f"Available rooms error: {str(e)}")

    # Guest Operations
    @task(2)
    def guest_operations(self):
        """Perform guest CRUD operations"""
        # Get CSRF token from guest list page
        response = self.client.get("/guest/")
        if response.status_code == 200:
            self.update_csrf_token(response)

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
                "postcode": "SW1A 1AA",
                "csrfmiddlewaretoken": self.csrf_token
            }

            # Create guest
            response = self.client.post("/guest/create/", data=guest_data)

            if response.status_code == 302:  # Successful redirect after creation
                # Extract guest ID from redirect URL
                redirect_url = response.headers.get('Location', '')
                if '/guest/' in redirect_url:
                    try:
                        self.guest_id = int(redirect_url.split('/guest/')[1].split('/')[0])

                        # Update guest
                        guest_data["first_name"] = f"Updated{random.randint(1, 1000)}"
                        guest_data["csrfmiddlewaretoken"] = self.csrf_token
                        self.client.post(f"/guest/{self.guest_id}/update/", data=guest_data)
                    except (ValueError, IndexError):
                        pass

    # Room Operations
    @task(2)
    def room_operations(self):
        """Perform room CRUD operations"""
        # Get CSRF token from room list page
        response = self.client.get("/room/")
        if response.status_code == 200:
            self.update_csrf_token(response)

            # Create room
            room_data = {
                "room_number": str(random.randint(100, 999)),
                "room_type": "STD",  # Using standard room type code
                "csrfmiddlewaretoken": self.csrf_token
            }

            response = self.client.post("/room/create/", data=room_data)

            if response.status_code == 302:  # Successful redirect after creation
                self.room_number = room_data["room_number"]

                # Update room
                if self.room_number:
                    room_data["room_type"] = "DLX"  # Change to deluxe
                    room_data["csrfmiddlewaretoken"] = self.csrf_token
                    self.client.post(f"/room/{self.room_number}/update/", data=room_data)

    # Room Type Operations
    @task(1)
    def room_type_operations(self):
        """Perform room type CRUD operations"""
        # Get CSRF token from room types list page
        response = self.client.get("/room-types/")
        if response.status_code == 200:
            self.update_csrf_token(response)

            # Create room type
            room_type_data = {
                "room_type_code": f"T{random.randint(1, 99)}",
                "room_type_name": f"Test Room Type {random.randint(1, 99)}",
                "price": str(random.randint(100, 500)),
                "deluxe": "true",
                "bath": "true",
                "separate_shower": "true",
                "maximum_guests": "2",
                "csrfmiddlewaretoken": self.csrf_token
            }

            response = self.client.post("/room-types/create/", data=room_type_data)

            if response.status_code == 302:  # Successful redirect after creation
                self.room_type_code = room_type_data["room_type_code"]

                # Update room type
                if self.room_type_code:
                    room_type_data["price"] = str(random.randint(100, 500))
                    room_type_data["csrfmiddlewaretoken"] = self.csrf_token
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
        self.cleanup()

    def weight_adjustment(self):
        """Dynamically adjust task weights based on response times"""
        stats = self.environment.stats

        # Get median response time for all requests
        total_median = stats.total.median_response_time

        if total_median > 5000:  # If median response time > 5s
            # Reduce frequency of heavy operations
            self.browse_available_rooms.weight = 1
            self.room_operations.weight = 1
        else:
            # Reset to normal weights
            self.browse_available_rooms.weight = 3
            self.room_operations.weight = 2

    def cleanup(self):
        """Handle cleanup operations with proper error handling"""
        try:
            if self.csrf_token:  # Only attempt cleanup if we were logged in
                # Delete created resources
                if self.guest_id:
                    with self.client.post(f"/guest/{self.guest_id}/delete/",
                                        catch_response=True) as response:
                        self.handle_response(response, "delete_guest")

                if self.room_number:
                    with self.client.post(f"/room/{self.room_number}/delete/",
                                        catch_response=True) as response:
                        self.handle_response(response, "delete_room")

                if self.room_type_code:
                    with self.client.post(f"/room-types/{self.room_type_code}/delete/",
                                        catch_response=True) as response:
                        self.handle_response(response, "delete_room_type")

                # Proper logout
                with self.client.get("/logout/",
                                   allow_redirects=True,
                                   catch_response=True) as response:
                    if response.status_code == 302:
                        redirect_url = response.headers.get('Location')
                        if redirect_url:
                            self.client.get(redirect_url)
        except Exception as e:
            logging.error(f"Cleanup error: {str(e)}")
        finally:
            # Clear session data
            self.csrf_token = None
            self.session_id = None
            self.client.cookies.clear()

        
