import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    server = os.getenv("DB_SERVER")
    database = os.getenv("DB_NAME")
    username = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    driver = os.getenv("DB_DRIVER", "ODBC Driver 18 for SQL Server")

    if not server or not database:
        raise ValueError("DB_SERVER and DB_NAME must be set in your .env file.")

    if username and password:
        connection_string = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"TrustServerCertificate=yes;"
        )
    else:
        connection_string = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"Trusted_Connection=yes;"
            f"TrustServerCertificate=yes;"
        )

    return pyodbc.connect(connection_string)


def safe_query(fetch_function, fallback):
    try:
        return fetch_function()
    except Exception as e:
        print(f"Database query error: {e}")
        return fallback


def get_table_count(table_name):
    allowed_tables = {
        "users",
        "services",
        "service_categories",
        "bookings",
        "support_workers"
    }

    if table_name not in allowed_tables:
        raise ValueError("Invalid table name.")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    count = cursor.fetchone()[0]
    conn.close()

    return int(count)


def get_user_count():
    return get_table_count("users")


def get_service_count():
    return get_table_count("services")


def get_category_count():
    return get_table_count("service_categories")


def get_booking_count():
    return get_table_count("bookings")


def get_support_worker_count():
    return get_table_count("support_workers")


def get_active_service_count():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM services WHERE is_active = 1")
    count = cursor.fetchone()[0]

    conn.close()
    return int(count)


def get_users():
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        id,
        first_name,
        last_name,
        email,
        role
    FROM users
    ORDER BY id
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    users = []

    for row in rows:
        users.append({
            "id": row.id,
            "first_name": row.first_name,
            "last_name": row.last_name,
            "email": row.email,
            "role": row.role
        })

    conn.close()
    return users


def get_ndis_services():
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT 
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


def get_all_services():
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT 
        s.id,
        s.name,
        s.description,
        s.is_active,
        c.name AS category_name
    FROM services s
    LEFT JOIN service_categories c ON s.category_id = c.id
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


def get_service_categories():
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        id,
        name
    FROM service_categories
    ORDER BY name
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    categories = []

    for row in rows:
        categories.append({
            "id": row.id,
            "name": row.name
        })

    conn.close()
    return categories


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


def get_bookings():
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        b.id,
        b.user_id,
        b.service_id,
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
            "user_id": row.user_id,
            "participant_name": f"{row.first_name or ''} {row.last_name or ''}".strip(),
            "service_id": row.service_id,
            "service_name": row.service_name or "No service",
            "booking_date": str(row.booking_date),
            "notes": row.notes,
            "status": status_name
        })

    conn.close()
    return bookings


def get_support_workers():
    conn = get_connection()
    cursor = conn.cursor()

    query = """
    SELECT
        sw.id,
        sw.first_name,
        sw.last_name,
        sw.email,
        sw.phone,
        s.name AS service_name
    FROM support_workers sw
    LEFT JOIN services s ON sw.service_id = s.id
    ORDER BY sw.last_name, sw.first_name
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    workers = []

    for row in rows:
        workers.append({
            "id": row.id,
            "first_name": row.first_name,
            "last_name": row.last_name,
            "email": row.email,
            "phone": row.phone,
            "service_name": row.service_name or "No assigned service"
        })

    conn.close()
    return workers


def build_database_context():
    user_count = safe_query(get_user_count, None)
    service_count = safe_query(get_service_count, None)
    active_service_count = safe_query(get_active_service_count, None)
    category_count = safe_query(get_category_count, None)
    booking_count = safe_query(get_booking_count, None)
    support_worker_count = safe_query(get_support_worker_count, None)

    users = safe_query(get_users, [])
    services = safe_query(get_ndis_services, [])
    categories = safe_query(get_service_categories, [])
    bookings = safe_query(get_booking_summary, [])
    support_workers = safe_query(get_support_workers, [])

    count_lines = []

    if user_count is not None:
        count_lines.append(f"- Total users: {user_count}")

    if service_count is not None:
        count_lines.append(f"- Total services: {service_count}")

    if active_service_count is not None:
        count_lines.append(f"- Active services: {active_service_count}")

    if category_count is not None:
        count_lines.append(f"- Total service categories: {category_count}")

    if booking_count is not None:
        count_lines.append(f"- Total bookings: {booking_count}")

    if support_worker_count is not None:
        count_lines.append(f"- Total support workers: {support_worker_count}")

    user_lines = []

    for user in users:
        user_lines.append(
            f"- User ID: {user['id']} | "
            f"Name: {user['first_name']} {user['last_name']} | "
            f"Email: {user['email']} | "
            f"Role: {user['role']}"
        )

    category_lines = []

    for category in categories:
        category_lines.append(
            f"- Category ID: {category['id']} | Name: {category['name']}"
        )

    service_lines = []

    for service in services:
        service_lines.append(
            f"- Service ID: {service['id']}\n"
            f"  Name: {service['name']}\n"
            f"  Category: {service['category']}\n"
            f"  Description: {service['description']}\n"
            f"  Active: {service['is_active']}"
        )

    booking_lines = []

    for item in bookings:
        booking_lines.append(
            f"- {item['status']}: {item['total']}"
        )

    worker_lines = []

    for worker in support_workers:
        worker_lines.append(
            f"- Support Worker ID: {worker['id']}\n"
            f"  Name: {worker['first_name']} {worker['last_name']}\n"
            f"  Email: {worker['email']}\n"
            f"  Phone: {worker['phone']}\n"
            f"  Assigned Service: {worker['service_name']}"
        )

    database_context = f"""
NDIS PORTAL DATABASE CONTEXT

DATABASE COUNTS:
{chr(10).join(count_lines) if count_lines else "No database count information found."}

USERS:
{chr(10).join(user_lines) if user_lines else "No users found."}

SERVICE CATEGORIES:
{chr(10).join(category_lines) if category_lines else "No service categories found."}

ACTIVE SERVICES:
{chr(10).join(service_lines) if service_lines else "No active services found."}

BOOKING SUMMARY:
{chr(10).join(booking_lines) if booking_lines else "No booking records found."}

SUPPORT WORKERS:
{chr(10).join(worker_lines) if worker_lines else "No support workers found."}
"""

    return database_context.strip()


def answer_direct_database_question(question):
    q = question.lower().strip()

    if "how many" in q and "user" in q:
        count = safe_query(get_user_count, None)
        if count is not None:
            return f"There are {count} users in the database."

    if (
        "show me your users" in q
        or "show users" in q
        or "list users" in q
        or "name of users" in q
        or "names of users" in q
        or "users of ndis" in q
        or "give me the name of users" in q
        or "give me users" in q
    ):
        users = safe_query(get_users, [])

        if not users:
            return "I could not find user records."

        lines = ["These are the users in the database:"]

        for user in users:
            lines.append(
                f"- {user['first_name']} {user['last_name']} "
                f"({user['role']})"
            )

        return "\n".join(lines)

    if "how many" in q and "service" in q:
        count = safe_query(get_service_count, None)
        active_count = safe_query(get_active_service_count, None)

        if count is not None and active_count is not None:
            return f"There are {count} services in the database. {active_count} of them are active."

        if count is not None:
            return f"There are {count} services in the database."

    if (
        "what services" in q
        or "available services" in q
        or "list services" in q
        or "show services" in q
        or "give me services" in q
    ):
        services = safe_query(get_ndis_services, [])

        if not services:
            return "I could not find active services."

        lines = ["These are the active services:"]

        for service in services:
            lines.append(
                f"- {service['name']} ({service['category']}): {service['description']}"
            )

        return "\n".join(lines)

    if "how many" in q and "category" in q:
        count = safe_query(get_category_count, None)
        if count is not None:
            return f"There are {count} service categories in the database."

    if (
        "what categories" in q
        or "service categories" in q
        or "list categories" in q
        or "show categories" in q
        or "give me categories" in q
    ):
        categories = safe_query(get_service_categories, [])

        if not categories:
            return "I could not find service categories."

        lines = ["These are the service categories:"]

        for category in categories:
            lines.append(f"- {category['name']}")

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
    ):
        bookings = safe_query(get_booking_summary, [])

        if not bookings:
            return "I could not find booking records."

        lines = ["Here is the booking summary:"]

        for item in bookings:
            lines.append(f"- {item['status']}: {item['total']}")

        return "\n".join(lines)

    if "how many" in q and ("support worker" in q or "worker" in q):
        count = safe_query(get_support_worker_count, None)
        if count is not None:
            return f"There are {count} support workers in the database."

    if (
        "support worker" in q
        or "support workers" in q
        or "show workers" in q
        or "list workers" in q
        or "give me workers" in q
    ):
        workers = safe_query(get_support_workers, [])

        if not workers:
            return "I could not find support workers."

        lines = ["These are the support workers:"]

        for worker in workers:
            lines.append(
                f"- {worker['first_name']} {worker['last_name']} "
                f"assigned to {worker['service_name']}"
            )

        return "\n".join(lines)

    return None