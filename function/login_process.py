from function.koneksi import get_db_connection

def proses_login(id_user, level):
    connection = get_db_connection()
    with connection.cursor() as cursor:
        if level == '' or level == '':
            cursor.execute('SELECT * FROM  WHERE  = %s', (id_user,))
            user = cursor.fetchone()
            if user:
                connection.close()
                return user[''], user[''], user[''], user['']
        
        if level == '' or level == '':
            cursor.execute('SELECT * FROM  WHERE  = %s', (id_user,))
            pengajar = cursor.fetchone()         
            if pengajar:
                connection.close()
                return pengajar[''], pengajar[''], pengajar[''], pengajar['']
        
        if level == '':
            cursor.execute('SELECT * FROM  WHERE  = %s', (id_user,))
            mhs = cursor.fetchone()                
            if mhs:
                connection.close()
                return mhs[''], mhs[''], mhs[''], ''
    return None

def get_session_user(username, password_hash):
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute('SELECT * FROM  WHERE  = %s AND  = %s', (username, password_hash))
        user = cursor.fetchone()
        if user:
            connection.close()
            return user_, no_id_, nama_, level_
        
        cursor.execute('SELECT * FROM  WHERE  = %s AND  = %s', (username, password_hash))
        pengajar = cursor.fetchone()
        if pengajar:
            connection.close()
            return user_, no_id_, nama_, level_

        cursor.execute('SELECT * FROM  WHERE  = %s AND  = %s', (username, password_hash))
        mhs = cursor.fetchone()
        if mhs:
            connection.close()
            return user_, no_id_, nama_, level_
        else:
            connection.close()
            user_ = None
            no_id_ = None
            nama_ = None 
            level_ = None
            return user_, no_id_, nama_, level_
    return None
    

