import sqlite3

conn = sqlite3.connect(r'backend\data\mediassist.db')
cur = conn.cursor()

# Get tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print('Tables:', tables)

for t in tables:
    cur.execute(f'PRAGMA table_info("{t}")')
    cols = cur.fetchall()
    print(f'\n--- {t} ---')
    for c in cols:
        print(f'  col: {c[1]}  type: {c[2]}')
    cur.execute(f'SELECT COUNT(*) FROM "{t}"')
    print(f'  Row count: {cur.fetchone()[0]}')
    # Show first row
    cur.execute(f'SELECT * FROM "{t}" LIMIT 1')
    print(f'  Sample: {cur.fetchone()}')

conn.close()

