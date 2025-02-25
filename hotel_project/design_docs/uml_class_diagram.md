classDiagram
    class RoomType {
        +String name
        +float price
        +String quality
        +String bathroomFeatures
        +int maxGuests
    }

    class Room {
        +int roomNumber
        +RoomType type
    }

    class Guest {
        +String fullName
        +String address
        +String phoneNumber
        +String email
    }

    class Reservation {
        +Date startDate
        +int lengthOfStay
        +int numberOfGuests
        +PromotionalDiscount discount
        +float price
        +String notes
        +boolean checkedIn
        +boolean checkedOut
        +Room room
        +Guest guest
    }

    class PromotionalDiscount {
        +String code
        +float percentage
    }

    class User {
        +String username
        +String password
        +String role
    }

    RoomType "1" -- "many" Room : defines
    Room "1" -- "many" Reservation : has
    Guest "1" -- "many" Reservation : makes
    PromotionalDiscount "0..1" -- "many" Reservation : applies
    User "1" -- "many" Reservation : manages
