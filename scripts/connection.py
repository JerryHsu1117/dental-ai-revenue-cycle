import snowflake.connector
from dotenv import load_dotenv
import os

load_dotenv()

def get_connection():
    # Returns a live Snowflake connection using .env credentials
    return snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema=os.getenv('SNOWFLAKE_SCHEMA')
    )

def execute_query(sql, params=None):
    # Run any SQL and return results as a list of dicts
    conn = get_connection()
    cur = conn.cursor(snowflake.connector.DictCursor)
    try:
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()
        conn.close()

def execute_many(sql, data):
    # Bulk insert — data is a list of tuples
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.executemany(sql, data)
        conn.commit()
    finally:
        cur.close()
        conn.close()

# Test connection
if __name__ == '__main__':
    result = execute_query('SELECT CURRENT_USER(), CURRENT_DATABASE()')
    print('Connection successful:', result)