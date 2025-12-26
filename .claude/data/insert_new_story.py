#!/usr/bin/env python3
"""Insert a new story into the story tree database."""
import sqlite3

conn = sqlite3.connect('.claude/data/story-tree.db')
cursor = conn.cursor()

cursor.execute('''
INSERT INTO story_nodes (
  id,
  title,
  description,
  capacity,
  stage,
  story
) VALUES (?, ?, ?, ?, ?, ?)
''', (
  '10.1.1',
  'Time Aggregation Query Foundation',
  '''**As a** developer implementing the aggregation view
**I want** to query the database for time entries grouped by bucket
**So that** we can calculate billable time totals per matter

**Acceptance Criteria:**
- [ ] SQL query groups activities by bucket_id with time sums
- [ ] Query supports date range filtering (start_date, end_date)
- [ ] Returns bucket name, total seconds, and activity count
- [ ] Handles null/empty bucket_id gracefully (groups as "Uncategorized")
- [ ] Query tested with sample data covering multiple buckets and date ranges

**Implementation Notes:**
- Use existing database.py methods as foundation
- Group by bucket_id from activities table
- Calculate SUM(duration_seconds) for each bucket
- Join with buckets table for display names
- Filter by start_time >= start_date AND start_time < end_date''',
  0,
  'concept',
  'Create the database query layer that will power the Client/Matter Time Aggregation View by grouping tracked activities by bucket (matter) and calculating time totals. This foundational query will handle date filtering and aggregation, preparing the data structure needed for the dashboard display. The implementation will extend the existing database.py module with a new method that lawyers can use to retrieve billable time summaries grouped by their imported matter folders.'
))

conn.commit()
conn.close()

print("Successfully inserted story 10.1.1")
