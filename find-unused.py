import os
import mysql.connector
from mysql.connector import Error
import docker
import argparse

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

def get_unused_images(connection, docker_client):
    """Query the database for unused images."""
    try:
        cursor = connection.cursor()
        query = """
            SELECT DISTINCT image_name, image_tag
            FROM docker_image_usage
            WHERE event_type = 'start'
        """
        cursor.execute(query)
        db_used_images = cursor.fetchall()

        # Cross-reference with local Docker images
        unused_images = []
        all_images = docker_client.images.list()

        for image in all_images:
            tags = image.tags if image.tags else ["<none>:<none>"]
            for tag in tags:
                image_name = tag.split(":")[0]
                image_tag = tag.split(":")[1] if ":" in tag else "latest"

                if (image_name, image_tag) not in db_used_images:
                    unused_images.append({
                        "id": image.id[:12],  # Shorten SHA ID to the first 12 characters
                        "name": image_name,
                        "tag": image_tag,
                        "size": image.attrs['Size']
                    })
        return unused_images
    except Error as e:
        print(f"Error querying database: {e}")
        return []

def format_size(size_in_bytes):
    """Convert size from bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_in_bytes < 1024:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= 1024

def find_unused_images(print_rm_commands=False):
    """Find unused Docker images and display details."""
    # Connect to MySQL
    db_connection = connect_to_db()
    if not db_connection:
        print("Unable to connect to the database. Exiting...")
        return

    # Initialize Docker client
    docker_client = docker.from_env()

    try:
        # Get unused images
        unused_images = get_unused_images(db_connection, docker_client)

        if not unused_images:
            print("No unused images found.")
            return

        # Sort images by size (largest first)
        unused_images.sort(key=lambda x: x['size'], reverse=True)

        print(f"{'Image ID':<15} {'Image Name':<30} {'Tag':<15} {'Size':<10}")
        print("-" * 80)

        for image in unused_images:
            print(f"{image['id']:<15} {image['name']:<30} {image['tag']:<15} {format_size(image['size']):<10}")

        # Print docker image rm commands if flag is set
        if print_rm_commands:
            print("\nDocker image removal commands:")
            for image in unused_images:
                print(f"docker image rm {image['id']}")
    except Exception as e:
        print(f"Error finding unused images: {e}")
    finally:
        if db_connection.is_connected():
            db_connection.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find unused Docker images.")
    parser.add_argument(
        "--print-rm-commands",
        action="store_true",
        help="Print docker image rm commands for unused images."
    )
    args = parser.parse_args()

    find_unused_images(print_rm_commands=args.print_rm_commands)

