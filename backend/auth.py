import sqlite3
import uuid
import os
import re
from passlib.hash import bcrypt

# ✅ NORMALIZE PASSWORD (CRITICAL FIX)
def normalize_password(password: str) -> str:
    return password[:72]

# ✅ SAFE VERIFY (REMOVED BAD FALLBACK)
def verify_password(password, hashed):
    try:
        password = normalize_password(password)
        return bcrypt.verify(password, hashed)
    except Exception:
        return False

DB_PATH = os.path.join(os.path.dirname(__file__), "database.sqlite")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            FOREIGN KEY(email) REFERENCES users(email)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS organizations (
            org_name TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            country TEXT,
            bio TEXT,
            number_of_employees INTEGER,
            ceo TEXT,
            goals TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS org_sessions (
            token TEXT PRIMARY KEY,
            org_name TEXT NOT NULL,
            FOREIGN KEY(org_name) REFERENCES organizations(org_name)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS org_financial_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_name TEXT NOT NULL,
            date TEXT,
            industry TEXT,
            stage TEXT,
            goal TEXT,
            revenue REAL,
            fixed_cost REAL,
            variable_cost REAL,
            total_cost REAL,
            profit REAL,
            cash_reserve REAL,
            debt REAL,
            growth_rate REAL,
            customer_count INTEGER,
            cac REAL,
            ltv REAL,
            profit_margin REAL,
            burn_rate REAL,
            runway_months REAL,
            debt_ratio REAL,
            risk_level TEXT,
            health_score REAL,
            recommendation TEXT,
            FOREIGN KEY(org_name) REFERENCES organizations(org_name)
        )
    ''')

    conn.commit()
    conn.close()

init_db()

# ---------------- USER AUTH ----------------

def signup(name, email, password):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return {"success": False, "error": "Email already exists"}

    password = normalize_password(password)
    hashed_pw = bcrypt.hash(password)

    cursor.execute(
        "INSERT INTO users (email, name, password) VALUES (?, ?, ?)",
        (email, name, hashed_pw)
    )

    token = str(uuid.uuid4())
    cursor.execute("INSERT INTO sessions (token, email) VALUES (?, ?)", (token, email))

    conn.commit()
    conn.close()

    return {"success": True, "token": token, "name": name}


def login(identifier, password):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email = ? COLLATE NOCASE OR name = ? COLLATE NOCASE",
        (identifier, identifier)
    )
    user = cursor.fetchone()

    if not user:
        conn.close()
        return {"success": False, "error": "Invalid email or username"}

    if not verify_password(password, user["password"]):
        conn.close()
        return {"success": False, "error": "Invalid password"}

    token = str(uuid.uuid4())
    cursor.execute("INSERT INTO sessions (token, email) VALUES (?, ?)", (token, user["email"]))

    conn.commit()
    conn.close()

    return {"success": True, "token": token, "name": user["name"], "email": user["email"]}


# ---------------- ORG AUTH ----------------

def org_signup(org_name, password, country=None, bio=None, number_of_employees=None, ceo=None, goals=None):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM organizations WHERE org_name = ?", (org_name,))
    if cursor.fetchone():
        conn.close()
        return {"success": False, "error": "Organization name already exists"}

    password = normalize_password(password)
    hashed_pw = bcrypt.hash(password)

    cursor.execute('''
        INSERT INTO organizations 
        (org_name, password, country, bio, number_of_employees, ceo, goals) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (org_name, hashed_pw, country, bio, number_of_employees, ceo, goals))

    token = str(uuid.uuid4())
    cursor.execute("INSERT INTO org_sessions (token, org_name) VALUES (?, ?)", (token, org_name))

    conn.commit()
    conn.close()

    return {"success": True, "token": token, "org_name": org_name}


def org_login(org_name, password):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM organizations WHERE org_name = ? COLLATE NOCASE", (org_name,))
    org = cursor.fetchone()

    if not org:
        conn.close()
        return {"success": False, "error": "Invalid organization name"}

    if not verify_password(password, org["password"]):
        conn.close()
        return {"success": False, "error": "Invalid password"}

    token = str(uuid.uuid4())
    cursor.execute("INSERT INTO org_sessions (token, org_name) VALUES (?, ?)", (token, org["org_name"]))

    conn.commit()
    conn.close()

    return {"success": True, "token": token, "org_name": org["org_name"]}


# ---------------- SESSION ----------------

def get_user_from_token(token):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT users.email, users.name 
        FROM sessions 
        JOIN users ON sessions.email = users.email 
        WHERE sessions.token = ?
    ''', (token,))

    user = cursor.fetchone()
    if user:
        conn.close()
        return {"email": user["email"], "name": user["name"], "type": "individual"}

    cursor.execute('''
        SELECT organizations.org_name 
        FROM org_sessions 
        JOIN organizations ON org_sessions.org_name = organizations.org_name 
        WHERE org_sessions.token = ?
    ''', (token,))

    org = cursor.fetchone()
    conn.close()

    if org:
        return {"org_name": org["org_name"], "type": "organization"}

    return None


def logout(token):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
    cursor.execute("DELETE FROM org_sessions WHERE token = ?", (token,))

    conn.commit()
    conn.close()

    return {"success": True}


# ---------------- SECURITY UPDATE ----------------

def update_security(email, current_password, new_email=None, new_password=None):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        return {"success": False, "error": "User not found"}

    if not verify_password(current_password, user["password"]):
        conn.close()
        return {"success": False, "error": "Incorrect current password"}

    if new_email and new_email != email:
        if not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
            conn.close()
            return {"success": False, "error": "Invalid email format"}

        cursor.execute("SELECT * FROM users WHERE email = ?", (new_email,))
        if cursor.fetchone():
            conn.close()
            return {"success": False, "error": "Email already in use"}

        cursor.execute("UPDATE sessions SET email = ? WHERE email = ?", (new_email, email))
        cursor.execute("UPDATE users SET email = ? WHERE email = ?", (new_email, email))
        email = new_email

    if new_password:
        if len(new_password) < 6:
            conn.close()
            return {"success": False, "error": "Password must be at least 6 characters"}

        new_password = normalize_password(new_password)
        hashed_pw = bcrypt.hash(new_password)
        cursor.execute("UPDATE users SET password = ? WHERE email = ?", (hashed_pw, email))

    conn.commit()
    conn.close()

    return {"success": True}
