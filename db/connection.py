# db/connection.py

import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# 🔧 EDIT THESE FOR YOUR SETUP
DB_USER = "root"
DB_PASSWORD = ""  # or "your_password"
DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_NAME = "healthdb"


def buildConnectionString() -> str:
    """
    Builds a SQLAlchemy connection string for MariaDB/MySQL using pymysql.
    """
    return (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@"
        f"{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )


@st.cache_resource
def getDbEngine() -> Engine:
    """
    Creates and caches a SQLAlchemy Engine.
    Streamlit will reuse this across reruns.
    """
    conn_str = buildConnectionString()
    engine = create_engine(conn_str, pool_pre_ping=True)
    return engine


def testConnection() -> bool:
    """
    Runs a simple `SELECT 1` to verify the DB connection works.
    Returns True if successful, False otherwise.
    """
    try:
        engine = getDbEngine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            _ = result.scalar()
        return True
    except Exception as e:
        # Let the caller decide how to display the error
        st.error(f"Database connection failed: {e}")
        return False
