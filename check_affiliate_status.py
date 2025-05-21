"""
Simple script to check the affiliate system status using direct SQL queries
"""

import os
import psycopg2
import sys
from datetime import datetime

# Connect to the database using the DATABASE_URL environment variable
db_url = os.environ.get('DATABASE_URL')
if not db_url:
    print("Error: DATABASE_URL environment variable not set")
    sys.exit(1)

try:
    # Connect to the database
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    print("Connected to database successfully")
    
    # Check status distribution of affiliates
    cursor.execute("SELECT status, COUNT(*) FROM affiliate GROUP BY status;")
    status_counts = cursor.fetchall()
    
    print("\nAffiliate Status Distribution:")
    print("------------------------------")
    for status, count in status_counts:
        print(f"{status}: {count}")
    
    # Check users without affiliates
    cursor.execute("""
        SELECT COUNT(*) FROM "user" u 
        WHERE NOT EXISTS (
            SELECT 1 FROM affiliate a WHERE a.email = u.email
        );
    """)
    users_without_affiliates = cursor.fetchone()[0]
    print(f"\nUsers without affiliates: {users_without_affiliates}")
    
    # Find any pending_terms affiliates (should be 0 after our changes)
    cursor.execute("SELECT id, name, email FROM affiliate WHERE status = 'pending_terms';")
    pending_affiliates = cursor.fetchall()
    
    if pending_affiliates:
        print("\nPending affiliates (should be empty after our changes):")
        print("------------------------------------------------------")
        for affiliate in pending_affiliates:
            print(f"ID: {affiliate[0]}, Name: {affiliate[1]}, Email: {affiliate[2]}")
    else:
        print("\nNo pending affiliates found - this is good!")
    
    # Display recently updated affiliates
    cursor.execute("""
        SELECT id, name, email, status, updated_at 
        FROM affiliate 
        ORDER BY updated_at DESC
        LIMIT 5;
    """)
    recent_affiliates = cursor.fetchall()
    
    print("\nRecently Updated Affiliates:")
    print("--------------------------")
    for affiliate in recent_affiliates:
        print(f"ID: {affiliate[0]}, Name: {affiliate[1]}")
        print(f"  Email: {affiliate[2]}, Status: {affiliate[3]}, Updated: {affiliate[4]}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error: {str(e)}")
    sys.exit(1)