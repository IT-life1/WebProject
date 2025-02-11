import psycopg2
from psycopg2 import OperationalError
import sys

def create_conn():
    """Create a connection to the PostgreSQL database."""
    conn = None
    try:
        # Update these parameters with your actual database credentials
        conn = psycopg2.connect(
            host="db",  # Replace with your database host (e.g., "localhost" or "db" for Docker)
            database="first",  # Replace with your database name
            user="postgres",  # Replace with your database username
            password="sova",  # Replace with your database password
            port=5432  # Default PostgreSQL port
        )
        print("Connection successful!")
        return conn
    except OperationalError as e:
        print(f"The error '{e}' occurred while connecting to the database.")
        sys.exit(1)

def test_query(conn):
    """Test a simple query to verify the connection."""
    try:
        cursor = conn.cursor()
        # Execute a simple query
        cursor.execute("SELECT version();")
        # Fetch and print the result
        db_version = cursor.fetchone()
        print(f"PostgreSQL Database Version: {db_version[0]}")
        
        # Test table existence
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        tables = cursor.fetchall()
        if tables:
            print("Tables in the database:")
            for table in tables:
                print(f"- {table[0]}")
        else:
            print("No tables found in the database.")
    except Exception as e:
        print(f"An error occurred while executing the query: {e}")
    finally:
        cursor.close()

def close_conn(conn):
    """Close the database connection."""
    if conn:
        conn.close()
        print("Database connection closed.")

if __name__ == "__main__":
    # Create a connection to the database
    connection = create_conn()
    
    if connection:
        # Test the connection by running a query
        test_query(connection)
        
        # Close the connection
        close_conn(connection)