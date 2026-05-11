import os
from typing import Dict, List, Optional

import pyodbc
from dotenv import load_dotenv

from logger_config import setup_logger


logger = setup_logger(__name__)

load_dotenv()

SERVICES_TABLE = "services"
BOOKINGS_TABLE = "bookings"


def get_connection():
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    username = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    driver = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")

    if not server or not database:
        raise ValueError("DB_SERVER and DB_NAME must be set in your .env file.")

    connection_parts = [
        f"DRIVER={{{driver}}}",
        f"SERVER={server}",
        f"DATABASE={database}",
        "TrustServerCertificate=yes",
        "Connection Timeout=5",
    ]

    if username and password:
        connection_parts.extend([
            f"UID={username}",
            f"PWD={password}",
        ])
    else:
        connection_parts.append("Trusted_Connection=yes")

    connection_string = ";".join(connection_parts) + ";"

    try:
        return pyodbc.connect(connection_string, timeout=5)
    except pyodbc.Error as exc:
        logger.error("Database connection failed: %s", exc)
        raise ConnectionError(
            "Could not connect to SQL Server. Make sure SQL Server is running "
            "and DB_SERVER, DB_NAME, DB_USER, and DB_PASSWORD are correct."
        ) from exc


def safe_query(fetch_function, fallback):
    try:
        return fetch_function()
    except Exception as e:
        logger.error("Database query error: %s", e)
        return fallback


def quote_identifier(identifier: str) -> str:
    return f"[{identifier.replace(']', ']]')}]"


def get_table_columns(table_name: str) -> Dict[str, str]:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = ?
        """,
        table_name,
    )

    columns = {
        row.COLUMN_NAME.lower(): row.COLUMN_NAME
        for row in cursor.fetchall()
    }

    conn.close()
    return columns


def pick_column(columns: Dict[str, str], candidates: List[str]) -> Optional[str]:
    for candidate in candidates:
        if candidate.lower() in columns:
            return columns[candidate.lower()]

    return None


def first_value(row, column: Optional[str], default=None):
    if not column:
        return default

    return getattr(row, column, default)


def normalize_status(status) -> str:
    if status is None:
        return "Unknown"

    try:
        status_value = int(status)
        return {
            0: "Pending",
            1: "Approved",
            2: "Cancelled",
        }.get(status_value, str(status))
    except (TypeError, ValueError):
        return str(status)


def get_service_columns() -> Dict[str, str]:
    return get_table_columns(SERVICES_TABLE)


def get_booking_columns() -> Dict[str, str]:
    return get_table_columns(BOOKINGS_TABLE)


def get_service_count():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(f"SELECT COUNT(*) FROM {quote_identifier(SERVICES_TABLE)}")
    count = cursor.fetchone()[0]

    conn.close()
    return int(count)


def get_active_service_count():
    columns = get_service_columns()
    active_col = pick_column(columns, ["is_active", "active", "enabled"])

    if not active_col:
        return get_service_count()

    conn = get_connection()
    cursor = conn.cursor()

    query = (
        f"SELECT COUNT(*) FROM {quote_identifier(SERVICES_TABLE)} "
        f"WHERE {quote_identifier(active_col)} = 1"
    )

    cursor.execute(query)
    count = cursor.fetchone()[0]

    conn.close()
    return int(count)


def get_booking_count():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(f"SELECT COUNT(*) FROM {quote_identifier(BOOKINGS_TABLE)}")
    count = cursor.fetchone()[0]

    conn.close()
    return int(count)


def get_ndis_services(limit=10):
    columns = get_service_columns()

    id_col = pick_column(columns, ["id", "service_id"])
    name_col = pick_column(columns, ["name", "service_name", "title"])
    description_col = pick_column(columns, ["description", "details", "service_description"])
    active_col = pick_column(columns, ["is_active", "active", "enabled"])

    select_parts = []

    for alias, column in {
        "id": id_col,
        "name": name_col,
        "description": description_col,
        "is_active": active_col,
    }.items():
        if column:
            select_parts.append(f"{quote_identifier(column)} AS {quote_identifier(alias)}")

    if not select_parts:
        select_parts.append("*")

    where_clause = f"WHERE {quote_identifier(active_col)} = 1" if active_col else ""
    order_clause = f"ORDER BY {quote_identifier(name_col)}" if name_col else ""

    query = f"""
    SELECT TOP ({int(limit)})
        {", ".join(select_parts)}
    FROM {quote_identifier(SERVICES_TABLE)}
    {where_clause}
    {order_clause}
    """

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    services = []

    for row in rows:
        services.append({
            "id": first_value(row, "id", ""),
            "name": first_value(row, "name", "Unnamed service"),
            "description": first_value(row, "description", ""),
            "is_active": bool(first_value(row, "is_active", True)),
        })

    return services


def get_booking_summary():
    columns = get_booking_columns()
    status_col = pick_column(columns, ["status", "booking_status", "state"])

    conn = get_connection()
    cursor = conn.cursor()

    if status_col:
        query = f"""
        SELECT
            {quote_identifier(status_col)} AS status,
            COUNT(*) AS total
        FROM {quote_identifier(BOOKINGS_TABLE)}
        GROUP BY {quote_identifier(status_col)}
        ORDER BY {quote_identifier(status_col)}
        """
    else:
        query = f"""
        SELECT
            'All bookings' AS status,
            COUNT(*) AS total
        FROM {quote_identifier(BOOKINGS_TABLE)}
        """

    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    summary = []

    for row in rows:
        summary.append({
            "status": normalize_status(row.status),
            "total": int(row.total),
        })

    return summary


def get_recent_bookings(limit=10):
    booking_columns = get_booking_columns()
    service_columns = get_service_columns()

    booking_id_col = pick_column(booking_columns, ["id", "booking_id"])
    booking_service_id_col = pick_column(booking_columns, ["service_id", "serviceid"])
    date_col = pick_column(booking_columns, ["booking_date", "date", "scheduled_date", "created_at"])
    notes_col = pick_column(booking_columns, ["notes", "note", "description"])
    status_col = pick_column(booking_columns, ["status", "booking_status", "state"])

    service_id_col = pick_column(service_columns, ["id", "service_id"])
    service_name_col = pick_column(service_columns, ["name", "service_name", "title"])

    can_join_services = bool(booking_service_id_col and service_id_col)

    select_parts = []

    for alias, column in {
        "id": booking_id_col,
        "service_id": booking_service_id_col,
        "booking_date": date_col,
        "notes": notes_col,
        "status": status_col,
    }.items():
        if column:
            select_parts.append(f"b.{quote_identifier(column)} AS {quote_identifier(alias)}")

    if can_join_services and service_name_col:
        select_parts.append(f"s.{quote_identifier(service_name_col)} AS service_name")

    if not select_parts:
        select_parts.append("b.*")

    join_clause = ""
    if can_join_services:
        join_clause = (
            f"LEFT JOIN {quote_identifier(SERVICES_TABLE)} s "
            f"ON b.{quote_identifier(booking_service_id_col)} = s.{quote_identifier(service_id_col)}"
        )

    order_clause = f"ORDER BY b.{quote_identifier(date_col)} DESC" if date_col else ""

    query = f"""
    SELECT TOP ({int(limit)})
        {", ".join(select_parts)}
    FROM {quote_identifier(BOOKINGS_TABLE)} b
    {join_clause}
    {order_clause}
    """

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    bookings = []

    for row in rows:
        bookings.append({
            "id": first_value(row, "id", ""),
            "service_id": first_value(row, "service_id", ""),
            "service_name": first_value(row, "service_name", "No service"),
            "booking_date": str(first_value(row, "booking_date", "")),
            "notes": first_value(row, "notes", ""),
            "status": normalize_status(first_value(row, "status", None)),
        })

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
        lines.append("Service records:")

        for service in services:
            lines.append(f"Service ID: {service['id']}")
            lines.append(f"Name: {service['name']}")
            lines.append(f"Description: {service['description']}")
            lines.append(f"Active: {service['is_active']}")
            lines.append("")
    else:
        lines.append("No services found.")

    return "\n".join(lines).strip()


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
            lines.append(f"{item['status']}: {item['total']}")
    else:
        lines.append("No booking summary found.")

    if recent_bookings:
        lines.append("")
        lines.append("Recent bookings:")

        for booking in recent_bookings:
            lines.append(f"Booking ID: {booking['id']}")
            lines.append(f"Service ID: {booking['service_id']}")
            lines.append(f"Service: {booking['service_name']}")
            lines.append(f"Date: {booking['booking_date']}")
            lines.append(f"Status: {booking['status']}")
            if booking["notes"]:
                lines.append(f"Notes: {booking['notes']}")
            lines.append("")

    return "\n".join(lines).strip()


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

    if "booking" in q and "service" in q:
        services = safe_query(lambda: get_ndis_services(limit=10), [])
        booking_count = safe_query(get_booking_count, None)
        summary = safe_query(get_booking_summary, [])
        recent_bookings = safe_query(lambda: get_recent_bookings(limit=10), [])

        lines = ["Here is the current database information."]

        if services:
            lines.append("")
            lines.append("Services:")
            for service in services:
                description = f": {service['description']}" if service["description"] else ""
                lines.append(f"{service['name']}{description}")
        else:
            lines.append("")
            lines.append("No active services found.")

        lines.append("")
        if booking_count is not None:
            lines.append(f"Total bookings: {booking_count}")

        if summary:
            lines.append("Booking summary:")
            for item in summary:
                lines.append(f"{item['status']}: {item['total']}")

        if recent_bookings:
            lines.append("")
            lines.append("Recent bookings:")
            for booking in recent_bookings:
                lines.append(
                    f"Booking {booking['id']}: {booking['service_name']} "
                    f"on {booking['booking_date']} - {booking['status']}"
                )

        return "\n".join(lines)

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
            description = f": {service['description']}" if service["description"] else ""
            lines.append(f"{service['name']}{description}")

        return "\n".join(lines)

    if "how many" in q and "booking" in q:
        count = safe_query(get_booking_count, None)

        if count is not None:
            return f"There are {count} bookings in the database."

    if "booking status" in q or "booking summary" in q:
        summary = safe_query(get_booking_summary, [])

        if not summary:
            return "I could not find booking records."

        lines = ["Here is the booking summary:"]

        for item in summary:
            lines.append(f"{item['status']}: {item['total']}")

        return "\n".join(lines)

    if (
        "show bookings" in q
        or "list bookings" in q
        or "give me bookings" in q
        or "what are the bookings" in q
        or "what bookings" in q
    ):
        recent_bookings = safe_query(lambda: get_recent_bookings(limit=10), [])

        if not recent_bookings:
            return "I could not find booking records."

        lines = ["Here are the recent bookings:"]

        for booking in recent_bookings:
            lines.append(
                f"Booking {booking['id']}: {booking['service_name']} "
                f"on {booking['booking_date']} - {booking['status']}"
            )

            if booking["notes"]:
                lines.append(f"Notes: {booking['notes']}")

        return "\n".join(lines)

    return None
