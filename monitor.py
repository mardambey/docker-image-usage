import docker
import mysql.connector
from mysql.connector import Error
import datetime
import os

# Get database connection info from environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "docker_monitor")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

# Connect to the database
def connect_to_db():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Insert event data into MySQL
def log_event_to_db(connection, image_name, image_tag, container_id, container_name, event_time, event_type):
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO docker_image_usage (image_name, image_tag, container_id, container_name, event_time, event_type) VALUES (%s, %s, %s, %s, %s, %s)",
            (image_name, image_tag, container_id, container_name, event_time, event_type)
        )
        connection.commit()
    except Error as e:
        print(f"Error inserting event into MySQL: {e}")

# Monitor Docker events
def monitor_docker_events():
    client = docker.from_env()
    db_connection = connect_to_db()
    if not db_connection:
        print("Unable to connect to the database. Exiting...")
        return

    try:
        print("Monitoring Docker events...")
        for event in client.events(decode=True):
            image_name = event['Actor']['Attributes'].get('image', 'unknown')
            image_tag = image_name.split(":")[1] if ":" in image_name else "latest"
            container_id = event.get('id', 'unknown')
            container_name = event['Actor']['Attributes'].get('name', 'unknown')
            event_time = datetime.datetime.fromtimestamp(event['time'])
            event_type = event['Action']
            if event['Type'] == 'container' and event['Action'] in ['start', 'die']:
                print(f"Logging event: {event_type} for image: {image_name}:{image_tag} at {event_time} from container {container_name}/{container_id}")
                log_event_to_db(db_connection, image_name, image_tag, container_id, container_name, event_time, event_type)
            else:
                print(f"Ignoring event: {event_type} for image: {image_name}:{image_tag} at {event_time} from container {container_name}/{container_id}")
    except Exception as e:
        print(f"Error monitoring Docker events: {e}")
    finally:
        if db_connection.is_connected():
            db_connection.close()

if __name__ == '__main__':
    monitor_docker_events()

