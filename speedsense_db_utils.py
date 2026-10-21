import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Database configuration (adjust environment variables or defaults as needed)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5433")
DB_NAME = os.getenv("DB_NAME", "speedsense_db")
DB_USER = os.getenv("DB_USER", "scraper_dev") 
DB_PASS = os.getenv("DB_PASS", "ScraperPass123")  


def get_db_connection():
    """Establishes and returns a connection to PostgreSQL."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        cursor_factory=RealDictCursor
    )

def insert_speed_reading(sensor_id: str, seq: int, speed_kmh: float, is_simulated: bool = True):
    """
    Inserts a validated speed reading into SPEED_READINGS.
    Checks location speed limit and creates a SPEEDING_EVENT if exceeded.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # 1. Insert reading
            query_reading = """
                INSERT INTO SPEED_READINGS (sensor_id, seq, speed_kmh)
                VALUES (%s, %s, %s)
                RETURNING reading_id, arrived_at;
            """
            cur.execute(query_reading, (sensor_id, seq, speed_kmh))
            reading = cur.fetchone()

            # 2. Lookup speed limit from sensor node's location
            query_limit = """
                SELECT l.speed_limit 
                FROM SENSOR_NODES s
                JOIN LOCATIONS l ON s.location_id = l.location_id
                WHERE s.sensor_id = %s;
            """
            cur.execute(query_limit, (sensor_id,))
            loc_result = cur.fetchone()
            speed_limit = loc_result["speed_limit"] if loc_result else 60 # Default urban threshold if unmapped

            # 3. Log speeding event if above threshold
            event_id = None
            if speed_kmh > speed_limit:
                query_event = """
                    INSERT INTO SPEEDING_EVENTS (sensor_id, speed_kmh, is_simulated_trigger)
                    VALUES (%s, %s, %s)
                    RETURNING event_id;
                """
                cur.execute(query_event, (sensor_id, speed_kmh, is_simulated))
                event_res = cur.fetchone()
                event_id = event_res["event_id"] if event_res else None

            conn.commit()
            return {
                "reading_id": reading["reading_id"],
                "arrived_at": reading["arrived_at"],
                "speed_limit": speed_limit,
                "is_speeding": speed_kmh > speed_limit,
                "event_id": event_id
            }
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
