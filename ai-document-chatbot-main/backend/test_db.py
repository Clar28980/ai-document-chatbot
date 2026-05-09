from database import get_ndis_services, get_booking_summary

print("Testing database connection...")

services = get_ndis_services()
print("\nServices:")
for service in services:
    print(f"- {service['name']} ({service['category']})")

bookings = get_booking_summary()
print("\nBooking Summary:")
for item in bookings:
    print(f"- {item['status']}: {item['total']}")