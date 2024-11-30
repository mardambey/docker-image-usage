import os
import mysql.connector
import re
from mysql.connector import Error

# Fetch database connection details from environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "docker_monitor")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")

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

def get_last_n_images(connection, n):
    cursor = connection.cursor()
    cursor.execute(
        "SELECT image_name, event_time FROM docker_image_usage ORDER BY event_time DESC LIMIT %s",
        (n,)
    )
    return cursor.fetchall()

def get_images_last_n_days(connection, days):
    cursor = connection.cursor()
    cursor.execute(
        "SELECT image_name, event_time FROM docker_image_usage WHERE event_time >= NOW() - INTERVAL %s DAY",
        (days,)
    )
    return cursor.fetchall()

def get_last_usage_of_image(connection, regex_pattern):
    cursor = connection.cursor()
    cursor.execute("SELECT image_name, event_time FROM docker_image_usage")
    results = cursor.fetchall()
    matches = [(image, time) for image, time in results if re.search(regex_pattern, image)]
    return sorted(matches, key=lambda x: x[1], reverse=True)

def query_tool():
    connection = connect_to_db()
    if not connection:
        return

    while True:
        print("\nQuery Options:")
        print("1. Show last N used images")
        print("2. Show images used during the last N days")
        print("3. When was a specified image last used? (regex search)")
        print("4. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            n = int(input("Enter N: "))
            results = get_last_n_images(connection, n)
            for image, time in results:
                print(f"Image: {image}, Last Used: {time}")
        elif choice == '2':
            days = int(input("Enter the number of days: "))
            results = get_images_last_n_days(connection, days)
            for image, time in results:
                print(f"Image: {image}, Last Used: {time}")
        elif choice == '3':
            pattern = input("Enter regex pattern for image name: ")
            results = get_last_usage_of_image(connection, pattern)
            for image, time in results:
                print(f"Image: {image}, Last Used: {time}")
        elif choice == '4':
            break
        else:
            print("Invalid choice. Try again.")

    if connection.is_connected():
        connection.close()

if __name__ == '__main__':
    query_tool()

