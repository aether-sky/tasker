import psycopg
import dotenv
import os
import common
import time

dotenv.load_dotenv()

host = 'db' #change to "localhost" if not running through docker
port = '5432'
dbname = 'tasker'
user = 'postgres'
password = str(os.getenv("POSTGRES_PASSWORD"))

CONN = None

STATUS_STARTED = 1
STATUS_FINISHED = 2
STATUS_FINISHED_EARLY = 3
STATUS_FINISHED_STALE = 4

def get_conn() -> None:
  global CONN
  if CONN == None or CONN.closed:
    CONN = psycopg.connect(
      host=host,
      port=port,
      dbname=dbname,
      user=user,
      password=password
    )
  return CONN

def read_sql(fname:str) -> list[str]:
  with open(fname,'r') as f:
    contents = f.read()
    return list(filter(len, contents.split(";")))

def clear_tables() -> None:
  conn = get_conn()
  with conn.cursor() as cur:
    stmts = read_sql("clear_tables.sql")
    for stmt in stmts:
      cur.execute(stmt)
  conn.commit()

def setup() -> None:
  conn = get_conn()
  #clear_tables()
  with conn.cursor() as cur:
    tables_cmds = read_sql("tables.sql")
    for t in tables_cmds:
      cur.execute(t)
  
  conn.commit()

def track_user(conn, user_id:int, username:str, displayname:str) -> None:
  print(f"Tracking new user {user_id} {username}")
  with conn.cursor() as cur:
    cur.execute("""INSERT INTO users (id, username, displayname) 
                   VALUES (%s, %s, %s)
                   ON CONFLICT (id) DO UPDATE 
                      SET username=EXCLUDED.username, 
                          displayname=EXCLUDED.username""", 
                (user_id, username, displayname))
  conn.commit()

def start_session(user:common.UserInfo, duration:int, intention:str, when:int, is_test:bool) -> None:
  conn = get_conn()
  track_user(conn, user.user_id, user.username, user.displayname)
  with conn.cursor() as cur:
    cur.execute("""INSERT INTO sessions (user_id, 
                                         session_date, 
                                         created_date, 
                                         duration, 
                                         status, 
                                         intention,
                                         is_test)
                   VALUES(%s, 
                          NOW() + INTERVAL '%s minutes', 
                          NOW(), 
                          %s, 
                          %s, 
                          %s,
                          %s)""", 
                (user.user_id, 
                 when, 
                 duration, 
                 STATUS_STARTED, 
                 intention,
                 is_test))
  conn.commit()

def end_session(user:common.UserInfo, resolution:str):
  conn = get_conn()
  with conn.cursor() as cur:
    cur.execute("""SELECT 
                     id, 
                     session_date, 
                     duration, 
                     status, 
                     intention 
                   FROM sessions 
                   WHERE user_id=%s 
                   ORDER BY created_date DESC 
                   LIMIT 1""", (user.user_id,))
    rows = cur.fetchall()
    if len(rows) == 0:
      return
    date = rows[0][1]
    now = time.time()
    #could check if it's too early, etc
    cur.execute("UPDATE sessions SET status=%s, resolution=%s WHERE id=%s", (STATUS_FINISHED, resolution, rows[0][0]))
  conn.commit()

def load_session_buttons()->[int]:
  conn = get_conn()
  rows = []
  with conn.cursor() as cur:
    cur.execute("""SELECT
                     user_id
                   FROM sessions
                   WHERE status=%s""", (STATUS_STARTED,))
    rows = cur.fetchall()
  conn.commit()
  if len(rows) == 0 or rows[0][0] is None:
    return []
  return common.flatten(rows)

def get_summary(user:common.UserInfo) -> str:
  conn = get_conn()
  rows = []
  with conn.cursor() as cur:
    cur.execute("""SELECT
                     SUM(duration), COUNT(*)
                   FROM sessions
                   WHERE user_id=%s
                     AND status=%s
                     AND NOT is_test""", (user.user_id,STATUS_FINISHED))
    rows = cur.fetchall()
  conn.commit()
  if len(rows) == 0 or rows[0][0] is None:
    return f"Failed to get summary {common.emoji('rainy')}"
  return f"{user.displayname} has focused for {rows[0][0]} minutes in {rows[0][1]} sessions!"

def close_stale_sessions():
  conn = get_conn()
  count = 0
  with conn.cursor() as cur:
    cur.execute("""UPDATE sessions
                   SET status=%s, resolution='session expired'
                   WHERE (NOW() > (session_date + (duration * 4) * INTERVAL '1 minute'))
                     AND status=%s
                   RETURNING id""", (STATUS_FINISHED_STALE, STATUS_STARTED))
    rows = common.flatten(cur.fetchall())
    count = len(rows)
    for id_ in common.flatten(cur.fetchall()):
      print(f"Closed stale session with id {id_}")
  conn.commit()
  return count
