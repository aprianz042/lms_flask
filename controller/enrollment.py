from function.koneksi import get_db_connection

def get_enrollment(id):
    connection = get_db_connection()
    if connection is None:
        return None, "Error connecting to the database."
    try:
        with connection.cursor() as cursor:
            sql_select = "SELECT * FROM materi WHERE id = %s;"
            cursor.execute(sql_select, (id))
            materi = cursor.fetchone() 

        return materi, None
    finally:
        connection.close()