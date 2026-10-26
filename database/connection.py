import mysql.connector
from mysql.connector import pooling
import os
import logging

logger = logging.getLogger(__name__)

# Connection pool holder
_pool = None

def init_db_pool(config):
    """
    Initializes the MySQL connection pool using configuration parameters.
    """
    global _pool
    if _pool is not None:
        return _pool
        
    try:
        # We first try to connect to make sure parameters are correct
        # Note: If database doesn't exist, we connect without db name first to create it
        temp_conn = mysql.connector.connect(
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD
        )
        cursor = temp_conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config.DB_NAME}")
        temp_conn.commit()
        cursor.close()
        temp_conn.close()
        
        # Now initialize connection pool with the database specified
        _pool = pooling.MySQLConnectionPool(
            pool_name="bizkpi_pool",
            pool_size=5,
            host=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD,
            database=config.DB_NAME
        )
        logger.info("MySQL Connection Pool initialized successfully.")
        return _pool
    except mysql.connector.Error as err:
        logger.error(f"Error connecting to MySQL: {err}")
        raise err

def get_db_connection():
    """
    Retrieves a connection from the connection pool.
    """
    global _pool
    if _pool is None:
        raise Exception("Database connection pool has not been initialized. Call init_db_pool(config) first.")
    return _pool.get_connection()

def execute_query(query, params=None, fetchone=False):
    """
    Executes a SELECT query and returns the result as a list of dictionaries (or a single dictionary).
    Protects against SQL injection via parameterized queries.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        # dictionary=True returns rows as dictionaries matching column names
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        if fetchone:
            result = cursor.fetchone()
        else:
            result = cursor.fetchall()
            
        return result
    except mysql.connector.Error as err:
        logger.error(f"Database query error: {err} | Query: {query} | Params: {params}")
        raise err
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def execute_update(query, params=None, return_id=False):
    """
    Executes an INSERT, UPDATE, or DELETE query.
    Protects against SQL injection via parameterized queries.
    """
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        
        if return_id:
            return cursor.lastrowid
        return cursor.rowcount
    except mysql.connector.Error as err:
        logger.error(f"Database update error: {err} | Query: {query} | Params: {params}")
        if conn:
            conn.rollback()
        raise err
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def execute_sql_file(filepath):
    """
    Helper to execute an SQL script file (used for database setup).
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"SQL file not found: {filepath}")
        
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        with open(filepath, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            
        # Split statements by semicolon, but handle cases where delimiters might be modified (keep it simple for schema.sql)
        statements = sql_script.split(';')
        for statement in statements:
            stmt = statement.strip()
            if stmt:
                cursor.execute(stmt)
                
        conn.commit()
        logger.info(f"Successfully executed SQL script: {filepath}")
    except mysql.connector.Error as err:
        logger.error(f"Error executing SQL file: {err}")
        if conn:
            conn.rollback()
        raise err
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
