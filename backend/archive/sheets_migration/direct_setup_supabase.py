#!/usr/bin/env python3
"""
Script to set up Supabase tables using direct PostgreSQL connection.
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get PostgreSQL connection string
pg_conn_str = os.getenv('POSTGRES_CONNECTION_STRING')
if not pg_conn_str:
    print("Error: POSTGRES_CONNECTION_STRING not found in .env file")
    sys.exit(1)

try:
    # Read SQL file
    with open('src/supabase_table_setup.sql', 'r') as f:
        sql = f.read()
    
    # Connect to PostgreSQL
    print(f"Connecting to PostgreSQL: {pg_conn_str[:40]}...")
    conn = psycopg2.connect(pg_conn_str)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Execute SQL commands one by one
    for sql_command in sql.split(';'):
        if sql_command.strip():
            try:
                print(f"Executing: {sql_command[:60]}...")
                cursor.execute(sql_command)
                print("Command executed successfully")
            except Exception as e:
                print(f"Error executing SQL command: {e}")
    
    # Close connection
    cursor.close()
    conn.close()
    print("Table setup completed!")
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)