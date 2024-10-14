import psycopg2
import logging
import os

logging.basicConfig(level=logging.DEBUG)

try:
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST')
    )
    logging.info("Successfully connected to PostgreSQL.")
    # Remember to close the connection when done
    conn.close()
except Exception as e:
    logging.error(f"Error connecting to PostgreSQL: {e}")
