import hashlib
import hmac
import os
import sqlite3
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from secrets import token_hex

DB = Path(os.environ.get("MERCADO_DB", Path(__file__).with_name("mercado.sqlite3")))
METHODS = ("Dinheiro", "PIX", "Débito", "Crédito", "Vale-alimentação", "Vale-refeição")
ROLES = {"owner": "Proprietário", "manager": "Gerente", "cashier": "Operador"}

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, name TEXT NOT NULL, login TEXT UNIQUE COLLATE NOCASE,
 password TEXT NOT NULL, role TEXT NOT NULL, active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS sessions (
 token TEXT PRIMARY KEY, user_id INTEGER REFERENCES users, expires INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS contacts (
 id INTEGER PRIMARY KEY, kind TEXT NOT NULL, name TEXT NOT NULL, document TEXT,
 phone TEXT, email TEXT, address TEXT, notes TEXT
);
CREATE TABLE IF NOT EXISTS products (
 id INTEGER PRIMARY KEY, sku TEXT UNIQUE COLLATE NOCASE, barcode TEXT UNIQUE,
 name TEXT NOT NULL, category TEXT NOT NULL, unit TEXT NOT NULL, cost INTEGER NOT NULL,
 price INTEGER NOT NULL, minimum INTEGER NOT NULL, supplier INTEGER REFERENCES contacts,
 tax TEXT, active INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS lots (
 id INTEGER PRIMARY KEY, product_id INTEGER NOT NULL REFERENCES products,
 code TEXT NOT NULL, expiry TEXT NOT NULL, received TEXT NOT NULL,
 quantity INTEGER NOT NULL CHECK(quantity >= 0), UNIQUE(product_id, code)
);
CREATE TABLE IF NOT EXISTS movements (
 id INTEGER PRIMARY KEY, lot_id INTEGER REFERENCES lots, user_id INTEGER REFERENCES users,
 happened TEXT NOT NULL, delta INTEGER NOT NULL, reason TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tills (
 id INTEGER PRIMARY KEY, user_id INTEGER REFERENCES users, number TEXT NOT NULL,
 opened TEXT NOT NULL, initial INTEGER NOT NULL, closed TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS one_till_per_operator ON tills(user_id) WHERE closed IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS one_operator_per_till ON tills(number) WHERE closed IS NULL;
CREATE TABLE IF NOT EXISTS counts (
 till_id INTEGER REFERENCES tills, method TEXT, expected INTEGER, counted INTEGER,
 PRIMARY KEY(till_id, method)
);
CREATE TABLE IF NOT EXISTS sales (
 id INTEGER PRIMARY KEY, till_id INTEGER REFERENCES tills, happened TEXT NOT NULL,
 method TEXT NOT NULL, total INTEGER NOT NULL, received INTEGER NOT NULL,
 discount INTEGER NOT NULL, approver INTEGER REFERENCES users,
 customer INTEGER REFERENCES contacts, request_key TEXT UNIQUE, fiscal TEXT,
 cancelled TEXT, cancel_reason TEXT, cancel_approver INTEGER REFERENCES users
);
CREATE TABLE IF NOT EXISTS sale_lines (
 id INTEGER PRIMARY KEY, sale_id INTEGER REFERENCES sales, lot_id INTEGER REFERENCES lots,
 name TEXT, category TEXT, quantity INTEGER, price INTEGER, cost INTEGER, discount INTEGER
);
CREATE TABLE IF NOT EXISTS purchases (
 id INTEGER PRIMARY KEY, supplier INTEGER REFERENCES contacts, product INTEGER REFERENCES products,
 quantity INTEGER, cost INTEGER, created TEXT, received TEXT, actual INTEGER,
 actual_cost INTEGER, notes TEXT
);
CREATE TABLE IF NOT EXISTS finance (
 id INTEGER PRIMARY KEY, kind TEXT, description TEXT, amount INTEGER, due TEXT, settled TEXT
);
CREATE TABLE IF NOT EXISTS audit (
 id INTEGER PRIMARY KEY, happened TEXT, user_id INTEGER REFERENCES users,
 action TEXT, detail TEXT
);
CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT NOT NULL);
INSERT OR IGNORE INTO config VALUES ('discount', '5');
INSERT OR IGNORE INTO config VALUES ('name', 'Mercado Central');
"""


def connect():
    connection = sqlite3.connect(DB, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def now():
    return datetime.now().isoformat(timespec="seconds")


def today():
    return date.today().isoformat()


def password_hash(password, salt=None):
    salt = salt or token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600_000)
    return f"{salt}:{digest.hex()}"


def authenticated(db, login, password):
    account = db.execute("SELECT * FROM users WHERE login=? AND active=1", (login,)).fetchone()
    saved = account["password"] if account else "0" * 32 + ":" + "0" * 64
    valid = hmac.compare_digest(saved, password_hash(password, saved.split(":")[0]))
    return account if valid else None


def audit(db, user, action, detail=""):
    db.execute("INSERT INTO audit(happened,user_id,action,detail) VALUES (?,?,?,?)",
               (now(), user, action, detail))


def money(value):
    try:
        amount = Decimal(value.replace(",", ".")) * 100
        if amount.is_finite() and 0 <= amount <= 999_999_999 and amount == int(amount):
            return int(amount)
    except (InvalidOperation, AttributeError):
        pass
    raise ValueError("Informe um valor monetário válido com até duas casas decimais.")


def number(value, minimum=0, maximum=1_000_000):
    try:
        parsed = int(value)
        if minimum <= parsed <= maximum:
            return parsed
    except (ValueError, TypeError):
        pass
    raise ValueError(f"Informe um número inteiro entre {minimum} e {maximum}.")


def calendar(value):
    try:
        return date.fromisoformat(value).isoformat()
    except (ValueError, TypeError):
        raise ValueError("Informe uma data válida.") from None


def change(db, lot_id, user, delta, reason):
    updated = db.execute("UPDATE lots SET quantity=quantity+? WHERE id=? AND quantity+?>=0",
                         (delta, lot_id, delta))
    if not updated.rowcount:
        raise ValueError("Lote inexistente ou saldo insuficiente.")
    db.execute("INSERT INTO movements(lot_id,user_id,happened,delta,reason) VALUES (?,?,?,?,?)",
               (lot_id, user, now(), delta, reason))


def receive(db, user, product, code, expiry, quantity, reason):
    lot = db.execute("SELECT * FROM lots WHERE product_id=? AND code=?", (product, code)).fetchone()
    if lot and lot["expiry"] != expiry:
        raise ValueError("A validade informada difere da validade cadastrada para este lote.")
    lot_id = lot["id"] if lot else db.execute(
        "INSERT INTO lots(product_id,code,expiry,received,quantity) VALUES (?,?,?,?,0)",
        (product, code, expiry, today())).lastrowid
    change(db, lot_id, user, quantity, reason)


def available_lots(db, product):
    return db.execute("""SELECT * FROM lots WHERE product_id=? AND quantity>0 AND expiry>=?
                         ORDER BY expiry, received, id""", (product, today())).fetchall()
