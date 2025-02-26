from locust import HttpUser, task, between
from datetime import datetime, timedelta
import random
import json

class HotelUser(HttpUser):
    wait_time = between(1, 3)  # Random wait between tasks
    
    def on_start(self):
        """Initialize user session."""
        # Login
        self.client.post("/login/", {
            "username": f"test_user_{random.randint(1, 1000)}",
            "password": "testpass123"
        })
        
        # Store some test data
        self.test_dates = [
            (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d')
            for i in range(1, 30)
        ]
        self.room_types = ["Single", "Double", "Suite"]

    @task(3)
    def view_homepage(self):
        """Simulate viewing the homepage."""
        self.client.get("/")

    @task(2)
    def search_rooms(self):
        """Simulate searching for available rooms."""
        check_in = random.choice(self.test_dates)
        check_out = (datetime.strptime(check_in, '%Y-%m-%d') + timedelta(days=random.randint(1, 7))).strftime('%Y-%m-%d')
        
        self.client.get(f"/search/?check_in={check_in}&check_out={check_out}&guests={random.randint(1, 4)}")

    @task(1)
    def make_reservation(self):
        """Simulate making a reservation."""
        # First search for available rooms
        check_in = random.choice(self.test_dates)
        check_out = (datetime.strptime(check_in, '%Y-%m-%d') + timedelta(days=random.randint(1, 7))).strftime('%Y-%m-%d')
        guests = random.randint(1, 4)
        
        # Get available rooms
        response = self.client.get(f"/api/available-rooms/?check_in={check_in}&check_out={check_out}&guests={guests}")
        
        if response.status_code == 200:
            # Try to make a reservation
            reservation_data = {
                "check_in": check_in,
                "check_out": check_out,
                "guests": guests,
                "room_type": random.choice(self.room_types),
                "special_requests": "No special requests"
            }
            
            self.client.post("/api/reservations/", json=reservation_data)

    @task(2)
    def view_room_details(self):
        """Simulate viewing room details."""
        room_type = random.choice(self.room_types)
        self.client.get(f"/rooms/{room_type}/")

    @task(1)
    def check_reservation_status(self):
        """Simulate checking reservation status."""
        # Assuming there's an endpoint to check reservations
        self.client.get("/api/my-reservations/")