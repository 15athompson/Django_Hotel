# Hotel Management System Design Documentation

## 1. Introduction
This document outlines the design specification for the Hotel Management System, based on the requirements provided.

## 2. Core Entities and Relationships
- **RoomType**: Defines the type of room (e.g., single, double, suite).
- **Room**: Represents individual rooms with a room number and type.
- **Guest**: Information about guests staying at the hotel.
- **Reservation**: Details of room reservations, including start date, length of stay, and associated guest.
- **PromotionalDiscount**: Discount codes and their percentage.
- **User**: System users with roles (Receptionist, Manager, IT Administrator).

## 3. UML Class Diagram
```mermaid
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
```

## 4. Database Schema
```mermaid
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
```

## 5. System Architecture
```mermaid
graph TD
    A[User Interface] --> B[Controller]
    B --> C[Service Layer]
    C --> D[Repository Layer]
    D --> E[Database]
```

## 6. Detailed Design
### 6.1 RoomType
- **Attributes**:
  - name: String
  - price: float
  - quality: String
  - bathroomFeatures: String
  - maxGuests: int

### 6.2 Room
- **Attributes**:
  - roomNumber: int
  - type: RoomType

### 6.3 Guest
- **Attributes**:
  - fullName: String
  - address: String
  - phoneNumber: String
  - email: String

### 6.4 Reservation
- **Attributes**:
  - startDate: Date
  - lengthOfStay: int
  - numberOfGuests: int
  - discount: PromotionalDiscount
  - price: float
  - notes: String
  - checkedIn: boolean
  - checkedOut: boolean
  - room: Room
  - guest: Guest

### 6.5 PromotionalDiscount
- **Attributes**:
  - code: String
  - percentage: float

### 6.6 User
- **Attributes**:
  - username: String
  - password: String
  - role: String

## 7. Sequence Diagrams
### 7.1 Room Reservation
```mermaid
sequenceDiagram
    participant R as Receptionist
    participant S as System
    participant D as Database

    R->>S: Reserve Room
    S->>D: Check Room Availability
    D-->>S: Room Available
    S->>R: Display Room Details
    R->>S: Confirm Reservation
    S->>D: Save Reservation
    D-->>S: Reservation Saved
    S-->>R: Reservation Confirmed
```

### 7.2 Guest Check-In
```mermaid
sequenceDiagram
    participant R as Receptionist
    participant S as System
    participant D as Database

    R->>S: Check-In Guest
    S->>D: Retrieve Reservation
    D-->>S: Reservation Details
    S->>R: Display Reservation Details
    R->>S: Confirm Check-In
    S->>D: Update Reservation Status
    D-->>S: Status Updated
    S-->>R: Check-In Confirmed
```

## 8. Activity Diagrams
### 8.1 Room Reservation Workflow
```mermaid
graph TD
    A[Start] --> B[Receptionist Logs In]
    B --> C[Search for Available Rooms]
    C --> D{Room Available?}
    D -- Yes --> E[Select Room]
    D -- No --> F[Notify No Available Rooms]
    E --> G[Register Guest]
    G --> H[Confirm Reservation]
    H --> I[Save Reservation]
    I --> J[End]
    F --> J
```

### 8.2 Guest Check-In Workflow
```mermaid
graph TD
    A[Start] --> B[Receptionist Logs In]
    B --> C[Search for Reservation]
    C --> D{Reservation Found?}
    D -- Yes --> E[Display Reservation Details]
    D -- No --> F[Notify No Reservation Found]
    E --> G[Confirm Check-In]
    G --> H[Update Reservation Status]
    H --> I[End]
    F --> I
```

## 9. Decision Tables
### 9.1 Room Availability Check
| Condition | Action |
|-----------|--------|
| Room is available | Display room details |
| Room is not available | Notify no available rooms |

### 9.2 Reservation Confirmation
| Condition | Action |
|-----------|--------|
| Reservation confirmed | Save reservation |
| Reservation not confirmed | End process |

## 10. References
- Requirements Specification Document
- UML Diagrams and ER Diagrams
- System Architecture Diagram
