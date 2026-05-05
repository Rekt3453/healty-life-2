#!/usr/bin/env python
import psycopg2

try:
    connection = psycopg2.connect(
        dbname='postgres',
        user='postgres.xpzrljaykpanthomlegn',
        password='licuadora33',
        host='aws-0-us-west-2.pooler.supabase.com',
        port='6543',
        connect_timeout=20,
        sslmode='require',
        options='-c search_path=public'
    )
    
    cursor = connection.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"Conexión exitosa a PostgreSQL")
    print(f"Versión: {version[0]}")
    
    cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;")
    tables = cursor.fetchall()
    print(f"\nTablas encontradas:")
    for table in tables:
        print(f"- {table[0]}")
    
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"Error de conexión: {e}")
    print(f"Tipo de error: {type(e).__name__}")
