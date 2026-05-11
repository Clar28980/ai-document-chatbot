from database import get_ndis_services, get_booking_summary, get_recent_bookings

print("Testing database connection...")

services = get_ndis_services()
print("\nServices:")
for service in services:
    description = f": {service['description']}" if service.get("description") else ""
    print(f"- {service['name']}{description}")

bookings = get_booking_summary()
print("\nBooking Summary:")
for item in bookings:
    print(f"- {item['status']}: {item['total']}")

recent_bookings = get_recent_bookings()
print("\nRecent Bookings:")
for booking in recent_bookings:
    print(
        f"- Booking {booking['id']}: {booking['service_name']} "
        f"on {booking['booking_date']} - {booking['status']}"
    )
