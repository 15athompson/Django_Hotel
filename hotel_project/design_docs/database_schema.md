erDiagram
    ROOM_TYPE {
        String name
        float price
        String quality
        String bathroomFeatures
        int maxGuests
    }

    ROOM {
        int roomNumber
        int roomTypeId
    }

    GUEST {
        String fullName
        String address
        String phoneNumber
        String email
    }

    RESERVATION {
        Date startDate
        int lengthOfStay
        int numberOfGuests
        int discountId
        float price
        String notes
        boolean checkedIn
        boolean checkedOut
        int roomId
        int guestId
    }

    PROMOTIONAL_DISCOUNT {
        String code
        float percentage
    }

    USER {
        String username
        String password
        String role
    }

    ROOM_TYPE ||--o{ ROOM : defines
    ROOM ||--o{ RESERVATION : has
    GUEST ||--o{ RESERVATION : makes
    PROMOTIONAL_DISCOUNT |o--o{ RESERVATION : applies
    USER ||--o{ RESERVATION : manages
