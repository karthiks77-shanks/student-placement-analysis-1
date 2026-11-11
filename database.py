import os
import pymysql
import sqlite3
from contextlib import contextmanager
from werkzeug.security import generate_password_hash

# Database Configuration
DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()  # 'mysql' or 'sqlite'
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASS = os.getenv("MYSQL_PASS", "")
MYSQL_DB = os.getenv("MYSQL_DB", "placement_db")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_PATH = os.path.join(BASE_DIR, "placement.db")

active_db_info = {"type": "sqlite", "message": "Using local SQLite database"}

def test_mysql_connection(host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER, password=MYSQL_PASS, database=MYSQL_DB):
    """Tests MySQL connectivity and creates the target database if missing."""
    try:
        # First connect without database to check credentials
        conn = pymysql.connect(host=host, port=port, user=user, password=password, autocommit=True)
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{database}`")
        conn.close()
        return True, f"Successfully connected to MySQL at {host}:{port} and verified database '{database}'."
    except Exception as e:
        return False, str(e)

def get_connection():
    global active_db_info
    if DB_TYPE == "mysql":
        try:
            conn = pymysql.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASS,
                database=MYSQL_DB,
                cursorclass=pymysql.cursors.DictCursor,
                autocommit=True
            )
            active_db_info = {"type": "mysql", "message": f"Connected to MySQL ({MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB})"}
            return conn, "mysql"
        except Exception as e:
            # Graceful fallback to SQLite
            active_db_info = {
                "type": "sqlite",
                "message": f"MySQL connection failed ({e}). Falling back to local SQLite database."
            }
            conn = sqlite3.connect(SQLITE_PATH)
            conn.row_factory = sqlite3.Row
            return conn, "sqlite"
    else:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        active_db_info = {"type": "sqlite", "message": "Connected to SQLite (placement.db)"}
        return conn, "sqlite"

@contextmanager
def get_db():
    conn, engine = get_connection()
    try:
        yield conn, engine
    finally:
        conn.close()

def init_db():
    with get_db() as (conn, engine):
        cursor = conn.cursor()
        if engine == "mysql":
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id INT AUTO_INCREMENT PRIMARY KEY,
                roll_number VARCHAR(30) NOT NULL UNIQUE,
                full_name VARCHAR(100) NOT NULL,
                department VARCHAR(50) NOT NULL,
                graduation_year INT NOT NULL,
                cgpa DECIMAL(3, 2) NOT NULL,
                active_backlogs INT DEFAULT 0,
                is_eligible BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                skill_id INT AUTO_INCREMENT PRIMARY KEY,
                skill_name VARCHAR(50) NOT NULL UNIQUE
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_skills (
                student_id INT NOT NULL,
                skill_id INT NOT NULL,
                PRIMARY KEY (student_id, skill_id),
                FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
                FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS placements (
                placement_id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                company_name VARCHAR(100) NOT NULL,
                role VARCHAR(100) NOT NULL,
                package_lpa DECIMAL(5, 2) NOT NULL,
                placement_date DATE NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'Offer Accepted',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
            );
            """)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                email VARCHAR(100) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'Admin',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cursor.execute("SELECT user_id FROM users WHERE username = 'admin'")
            if not cursor.fetchone():
                admin_hash = generate_password_hash("admin123")
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, role)
                    VALUES (%s, %s, %s, %s)
                """, ("admin", "admin@goldenrice.edu", admin_hash, "Admin"))
        else:
            cursor.executescript("""
            CREATE TABLE IF NOT EXISTS students (
                student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_number TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                department TEXT NOT NULL,
                graduation_year INTEGER NOT NULL,
                cgpa REAL NOT NULL,
                active_backlogs INTEGER DEFAULT 0,
                is_eligible INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS skills (
                skill_id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name TEXT UNIQUE NOT NULL
            );
            CREATE TABLE IF NOT EXISTS student_skills (
                student_id INTEGER NOT NULL,
                skill_id INTEGER NOT NULL,
                PRIMARY KEY (student_id, skill_id),
                FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
                FOREIGN KEY (skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS placements (
                placement_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                company_name TEXT NOT NULL,
                role TEXT NOT NULL,
                package_lpa REAL NOT NULL,
                placement_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Offer Accepted',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'Admin',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            cursor.execute("SELECT user_id FROM users WHERE username = 'admin'")
            if not cursor.fetchone():
                admin_hash = generate_password_hash("admin123")
                cursor.execute("""
                    INSERT INTO users (username, email, password_hash, role)
                    VALUES (?, ?, ?, ?)
                """, ("admin", "admin@goldenrice.edu", admin_hash, "Admin"))
            conn.commit()
