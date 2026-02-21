import mysql.connector

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",   # <-- change if you set a password
        database="bargain_db"
    )
import sqlite3

def get_connection():
    conn = sqlite3.connect("bargain.db")
    conn.row_factory = sqlite3.Row   # IMPORTANT
    return conn