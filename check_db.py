import sqlite3; conn = sqlite3.connect('instance/homestay.db'); cursor = conn.cursor(); cursor.execute('SELECT count(*) FROM statistics'); print('Stats count:', cursor.fetchone()[0]); conn.close()
