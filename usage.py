import traceback
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

def get_last_used_date_and_container(connection, image_name):
    """Query the database for the last usage date and container name of a given image."""
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT event_time, container_name
            FROM docker_image_usage
            WHERE image_name LIKE %s
            ORDER BY event_time DESC
            LIMIT 1
            """,
            (f"{image_name}%",)  # Match images with the same name, regardless of tag
        )
        result = cursor.fetchone()
        if result:
            last_used, container_name = result
            return last_used.strftime('%m/%d/%Y'), container_name
        return "Never Used", "N/A"
    except Error as e:
        print(f"Error querying database: {e}")
        return "Error", "Error"

def check_image_usage():
    """Cross-reference Docker images with their last usage date and container."""
    # Connect to MySQL
    db_connection = connect_to_db()
    if not db_connection:
        print("Unable to connect to the database. Exiting...")
        return

    # Initialize Docker client
    docker_client = docker.from_env()

    try:
        # Get a list of all images on the local machine
        images = docker_client.images.list()
        
        # Collect data for sorting
        image_data = []

        for image in images:
            # Extract image name and tags
            image_tags = image.tags if image.tags else ["<none>:<none>"]
            for tag in image_tags:
                image_name = tag.split(":")[0]
                image_tag = tag.split(":")[1] if ":" in tag else "latest"

                # Get the last used date and container name from the database
                last_used, container_name = get_last_used_date_and_container(db_connection, image_name)
                if not container_name:
                    container_name = "N/A"
                if not last_used or last_used == "Never Used":
                    last_used_sortable = None  # Use None for proper sorting
                else:
                    last_used_sortable = datetime.strptime(last_used, '%m/%d/%Y')

                image_data.append({
                    "image_name": image_name,
                    "image_tag": image_tag,
                    "last_used": last_used,
                    "last_used_sortable": last_used_sortable,
                    "container_name": container_name
                })

        # Sort images by last used date (None values are placed at the end)
        image_data.sort(key=lambda x: x["last_used_sortable"] or datetime.min, reverse=True)

        # Print the sorted results
        print(f"{'Image Name':<50} {'Tag':<20} {'Last Used':<30} {'Container Name':<30}")
        print("-" * 130)
        for data in image_data:
            print(f"{data['image_name']:<50} {data['image_tag']:<20} {data['last_used']:<30} {data['container_name']:<30}")
    except Exception as e:
        print(f"Error while checking Docker images: {e}")
        print(traceback.format_exc())
    finally:
        if db_connection.is_connected():
            db_connection.close()

if __name__ == "__main__":
    check_image_usage()

