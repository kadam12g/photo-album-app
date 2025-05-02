#!/usr/bin/env python3

import time
import logging
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

logger = logging.getLogger(__name__)

def wait_for_db(db, max_retries=30, retry_interval=2):
    """
    Wait for database to be available
    
    Args:
        db: SQLAlchemy database instance
        max_retries: Maximum number of connection attempts
        retry_interval: Time in seconds between retries
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    logger.info("Waiting for database connection...")
    
    for attempt in range(max_retries):
        try:
            # Try a simple query
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection established!")
            return True
        except OperationalError as e:
            logger.warning(f"Database connection attempt {attempt + 1}/{max_retries} failed: {e}")
            time.sleep(retry_interval)
    
    logger.error(f"Could not connect to database after {max_retries} attempts")
    return False
