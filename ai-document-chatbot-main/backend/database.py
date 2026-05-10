import os
import pyodbc
from dotenv import load_dotenv
from logger_config import setup_logger

logger = setup_logger(__name__)

load_dotenv()


def get_connection():
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    username = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    driver = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")

    if not server or not database:
        raise ValueError("DB_SERVER and DB_NAME must be set in your .env file.")

    connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"TrustServerCertificate=yes;"
    )

    return pyodbc.connect(connection_string)


def safe_query(fetch_function, fallback):
    try:
        return fetch_function()
    except Exception as e:
        logger.error("Database query error: %s", e)
        return fallback


def get_service_count():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM services")
    count = cursor.fetchone()[0]

    conn.close()
    return int(count)


def get_active_service_count():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM services WHERE is_active = 1")
    count = cursor.fetchone()[0]

    conn.close()
    return int(count)


def get_booking_count():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM bookings")
    count = cursor.fetchone()[0]

    conn.close()
    return int(count)


def get_ndis_services(limit=10):
    conn = get_connection()
    cursor = conn.cursor()

    query = f"""
    SELECT TOP {limit}
        s.id,
        s.name,
        s.description,
        s.is_active,
        c.name AS category_name
    FROM services s
    LEFT JOIN service_categories c ON s.category_id = c.id
    WHERE s.is_active = 1
    ORDER BY c.name, s.name
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    services = []

    for row in rows:
        services.append({
            "id": row.id,
            "name": row.name,
            "description": row.description,
            "is_active": bool(row.is_active),
            "category": row.category_name or "No category"
        })

    conn.close()
    return services


def get_booking_summary():
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT 
        status,
        COUNT(*) AS total
    FROM bookings
    GROUP BY status
    ORDER BY status
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    summary = []

    for row in rows:
        status_value = int(row.status)

        status_name = {
            0: "Pending",
            1: "Approved",
            2: "Cancelled"
        }.get(status_value, "Unknown")

        summary.append({
            "status": status_name,
            "total": int(row.total)
        })

    conn.close()
    return summary


def get_recent_bookings(limit=10):
    conn = get_connection()
    cursor = conn.cursor()

    query = f"""
    SELECT TOP {limit}
        b.id,
        b.booking_date,
        b.notes,
        b.status,
        u.first_name,
        u.last_name,
        s.name AS service_name
    FROM bookings b
    LEFT JOIN users u ON b.user_id = u.id
    LEFT JOIN services s ON b.service_id = s.id
    ORDER BY b.booking_date DESC
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    bookings = []

    for row in rows:
        status_value = int(row.status)

        status_name = {
            0: "Pending",
            1: "Approved",
            2: "Cancelled"
        }.get(status_value, "Unknown")

        bookings.append({
            "id": row.id,
            "participant_name": f"{row.first_name or ''} {row.last_name or ''}".strip(),
            "service_name": row.service_name or "No service",
            "booking_date": str(row.booking_date),
            "notes": row.notes,
            "status": status_name
        })

    conn.close()
    return bookings


def detect_database_topic(question: str) -> str:
    q = question.lower()

    if any(word in q for word in ["booking", "bookings", "appointment", "appointments", "status"]):
        return "bookings"

    if any(word in q for word in ["service", "services", "ndis service", "available service"]):
        return "services"

    return "services_and_bookings"


def build_services_context():
    service_count = safe_query(get_service_count, None)
    active_service_count = safe_query(get_active_service_count, None)
    services = safe_query(lambda: get_ndis_services(limit=10), [])

    lines = ["SERVICES DATABASE CONTEXT"]

    if service_count is not None:
        lines.append(f"Total services: {service_count}")

    if active_service_count is not None:
        lines.append(f"Active services: {active_service_count}")

    if services:
        lines.append("")
        lines.append("Active service records:")

        for service in services:
            lines.append(
                f"- Service ID: {service['id']}\n"
                f"  Name: {service['name']}\n"
                f"  Category: {service['category']}\n"
                f"  Description: {service['description']}\n"
                f"  Active: {service['is_active']}"
            )
    else:
        lines.append("No active services found.")

    return "\n".join(lines)


def build_bookings_context():
    booking_count = safe_query(get_booking_count, None)
    summary = safe_query(get_booking_summary, [])
    recent_bookings = safe_query(lambda: get_recent_bookings(limit=10), [])

    lines = ["BOOKINGS DATABASE CONTEXT"]

    if booking_count is not None:
        lines.append(f"Total bookings: {booking_count}")

    if summary:
        lines.append("")
        lines.append("Booking summary:")

        for item in summary:
            lines.append(f"- {item['status']}: {item['total']}")
    else:
        lines.append("No booking summary found.")

    if recent_bookings:
        lines.append("")
        lines.append("Recent bookings:")

        for booking in recent_bookings:
            lines.append(
                f"- Booking ID: {booking['id']} | "
                f"Participant: {booking['participant_name']} | "
                f"Service: {booking['service_name']} | "
                f"Date: {booking['booking_date']} | "
                f"Status: {booking['status']}"
            )

    return "\n".join(lines)


def build_database_context(question: str = ""):
    topic = detect_database_topic(question)

    logger.info("Database topic detected: %s", topic)

    if topic == "services":
        return build_services_context()

    if topic == "bookings":
        return build_bookings_context()

    return build_services_context() + "\n\n---\n\n" + build_bookings_context()


def answer_direct_database_question(question):
    q = question.lower().strip()

    if "how many" in q and "service" in q:
        count = safe_query(get_service_count, None)
        active_count = safe_query(get_active_service_count, None)

        if count is not None and active_count is not None:
            return f"There are {count} services in the database. {active_count} are active."

        if count is not None:
            return f"There are {count} services in the database."

    if (
        "what services" in q
        or "available services" in q
        or "list services" in q
        or "show services" in q
        or "give me services" in q
    ):
        services = safe_query(lambda: get_ndis_services(limit=10), [])

        if not services:
            return "I could not find active services."

        lines = ["These are the active services:"]

        for service in services:
            lines.append(
                f"- {service['name']} ({service['category']}): {service['description']}"
            )

        return "\n".join(lines)

    if "how many" in q and "booking" in q:
        count = safe_query(get_booking_count, None)

        if count is not None:
            return f"There are {count} bookings in the database."

    if (
        "booking summary" in q
        or "booking status" in q
        or "show bookings" in q
        or "list bookings" in q
        or "give me bookings" in q
        or "what are the bookings" in q
        or "what bookings" in q
    ):
        summary = safe_query(get_booking_summary, [])

        if not summary:
            return "I could not find booking records."

        lines = ["Here is the booking summary:"]

        for item in summary:
            lines.append(f"- {item['status']}: {item['total']}")

        return "\n".join(lines)

    return None