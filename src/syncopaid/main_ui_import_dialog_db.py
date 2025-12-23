"""
Database operations for client/matter import.

Handles saving imported client and matter data to the database.
"""


def save_import_to_database(database, import_result):
    """Save imported clients and matters to database."""
    with database._get_connection() as conn:
        cursor = conn.cursor()

        # Build client ID map
        client_ids = {}
        for client in import_result.clients:
            cursor.execute("""
                INSERT OR IGNORE INTO clients (display_name, folder_path)
                VALUES (?, ?)
            """, (client.display_name, client.folder_path))

            cursor.execute(
                "SELECT id FROM clients WHERE display_name = ?",
                (client.display_name,)
            )
            row = cursor.fetchone()
            if row:
                client_ids[client.display_name] = row[0]

        # Insert matters
        for matter in import_result.matters:
            client_id = client_ids.get(matter.client_display_name)
            if client_id:
                cursor.execute("""
                    INSERT OR IGNORE INTO matters
                    (client_id, display_name, folder_path)
                    VALUES (?, ?, ?)
                """, (client_id, matter.display_name, matter.folder_path))

        conn.commit()
