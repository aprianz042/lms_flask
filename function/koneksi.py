import pymysql
import os

host = os.getenv('DB_HOST')
user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
database = os.getenv('DB_DATABASE')

def get_db_connection():
    try:
        connection = pymysql.connect(host=host,
                                       user=user,
                                       password=password,
                                       database=database,
                                       cursorclass=pymysql.cursors.DictCursor)
        return connection
    except pymysql.MySQLError as e:
        print(f"Error connecting to MySQL: {e}")
        return None