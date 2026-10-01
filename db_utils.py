import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection(db_name='agri_intelligence'):
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASS", ""),
            database=db_name,
            connection_timeout=3
        )
        return conn
    except mysql.connector.Error as err:
        print(f"[db_utils] MySQL Error: {err}")
        return None

def init_db():
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASS", "")
        )
    except mysql.connector.Error as err:
        print(f"[db_utils] Could not connect to MySQL server: {err}")
        print("[db_utils] Please ensure MySQL is running (e.g. in XAMPP or local service) on port 3306.")
        return False

    cursor = conn.cursor()
    
    with open('schema.sql', 'r', encoding='utf-8') as f:
        sql_file = f.read()
        sql_commands = sql_file.split(';')
        
    for command in sql_commands:
        clean_command = command.strip()
        if clean_command:
            try:
                cursor.execute(clean_command)
            except mysql.connector.Error as err:
                print(f"[db_utils] Command notice/error: {clean_command[:60]}... -> {err}")
            
    conn.commit()
    cursor.close()
    conn.close()
    print("[db_utils] Database, Tables, and Seed Data Initialized Successfully!")
    return True

if __name__ == "__main__":
    init_db()
