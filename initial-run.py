import os
import mysql.connector
from mysql.connector import Error
import docker
from datetime import datetime

# Fetch database connection details from environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "docker_monitor")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

def connect_to_db():
    """Establish a connection to the MySQL database."""
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

def insert_running_container(connection, image_name, image_tag, container_id, container_name, event_time, event_type):
    """Insert an entry for a currently running container into the database."""
    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO docker_image_usage (image_name, image_tag, container_id, container_name, event_time, event_type)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (image_name, image_tag, container_id, container_name, event_time, event_type))
        connection.commit()
        print(f"Inserted running container: {container_name} (Image: {image_name}:{image_tag})")
    except Error as e:
        print(f"Error inserting running container into MySQL: {e}")

def update_running_containers():
    """Check for currently running containers and log their usage."""
    # Connect to MySQL
    db_connection = connect_to_db()
    if not db_connection:
        print("Unable to connect to the database. Exiting...")
        return

    # Initialize Docker client
    docker_client = docker.from_env()

    try:
        # Get a list of all running containers
        containers = docker_client.containers.list(filters={"status": "running"})

        for container in containers:
            image_name = container.image.tags[0].split(":")[0] if container.image.tags else "<none>"
            image_tag = container.image.tags[0].split(":")[1] if container.image.tags and ":" in container.image.tags[0] else "latest"
            container_id = container.id
            container_name = container.name
            event_time = datetime.now()  # Current timestamp
            event_type = "start"  # Indicate the container is running

            insert_running_container(
                db_connection,
                image_name,
                image_tag,
                container_id,
                container_name,
                event_time,
                event_type
            )
    except Exception as e:
        print(f"Error while checking running containers: {e}")
    finally:
        if db_connection.is_connected():
            db_connection.close()

if __name__ == "__main__":
    update_running_containers()

