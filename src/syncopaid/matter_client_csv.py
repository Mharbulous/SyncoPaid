"""CSV import/export utilities for matters."""
import csv
from syncopaid.database import Database


def export_matters_csv(db: Database, csv_path: str):
    """Export all matters to CSV file."""
    matters = db.get_matters(status='all')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['matter_number', 'client_name', 'description', 'status'])
        writer.writeheader()
        for matter in matters:
            writer.writerow({
                'matter_number': matter['matter_number'],
                'client_name': matter.get('client_name', ''),
                'description': matter.get('description', ''),
                'status': matter['status']
            })


def import_matters_csv(db: Database, csv_path: str):
    """Import matters from CSV file."""
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Find or create client
            client_id = None
            client_name = row.get('client_name', '').strip()
            if client_name:
                for c in db.get_clients():
                    if c['name'] == client_name:
                        client_id = c['id']
                        break
                if client_id is None:
                    client_id = db.insert_client(name=client_name)

            try:
                db.insert_matter(
                    matter_number=row['matter_number'],
                    client_id=client_id,
                    description=row.get('description', '').strip() or None,
                    status=row.get('status', 'active')
                )
            except Exception:
                pass  # Skip duplicates
