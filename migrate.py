
import sqlite3

DB_NAME = 'service_auto_web.db'

def add_column_if_missing(cursor, table, column, col_type):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [info[1] for info in cursor.fetchall()]
    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
        print(f"Coloana '{column}' adăugată în tabelul '{table}'.")

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Tabel masini
add_column_if_missing(cursor, 'masini', 'motorizare', 'TEXT')
add_column_if_missing(cursor, 'masini', 'cod_motor', 'TEXT')

# Tabel reparatii
add_column_if_missing(cursor, 'reparatii', 'numar_km', 'TEXT')
add_column_if_missing(cursor, 'reparatii', 'data', 'TEXT')

# Tabel programari
add_column_if_missing(cursor, 'programari', 'ora_start', 'TEXT')
add_column_if_missing(cursor, 'programari', 'ora_end', 'TEXT')

conn.commit()
conn.close()
print("Migrare completă!")
