# ============================================================================
# FILE NAME     : sub_function.py
# AUTHOR        : DONG XUAN HIEN
# DIVISION      : SDG2 - KVHS (Kefico Vietnam Hanoi Software)
# DESCRIPTION   : Storage sub function
# HISTORY       : 09/03/2026
# ============================================================================

from cfg import *

# ----------------------- Helpers -----------------------
'''
- Read YYYY_MM_DD from the file name & return a datetime (y,m,d)
- Used to decide whether to open this file based on last processed time
'''
def get_excel_file_date(filename: str):
    """Extract file date from 'YYYY_MM_DD.xlsx'."""
    m = DATE_FILE_RE.search(filename)
    if not m:
        return None
    y, mm, dd = map(int, m.groups())
    return datetime(y, mm, dd)


'''
- Tries to several common date/time formats, otherwise uses pandas to parse
- Return a python datetime (seconds precision)
- If it can't parse, return None & the row is skipped (because Time is the PRIMARY KEY)
'''
def parse_time(value: str):
    """Try to parse time from Excel cell."""
    if not value:
        return None
    value = str(value).strip()

    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%d/%m/%Y %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y/%m/%d %H:%M"
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(value, fmt)
            return dt.replace(microsecond=0)
        except:
            pass

    try:
        dt = pd.to_datetime(value, errors="coerce")
        if pd.isna(dt):
            return None
        return dt.to_pydatetime().replace(microsecond=0)
    except:
        return None


'''
- Create the tickets table if it doesn't exist
- PRIMARY KEY is Time 
'''
def ensure_table(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ticket_log_table (
            Time TEXT PRIMARY KEY,
            Name TEXT,
            Note TEXT,
            Project_Name TEXT,
            Requester TEXT
        )
    """)
    conn.commit()


'''
- Get last time from the table
'''
def get_last_time_from_db(conn):
    """Return latest Time field from DB (max Time)."""
    cur = conn.cursor()
    cur.execute("SELECT MAX(Time) FROM ticket_log_table")
    row = cur.fetchone()
    if row and row[0]:
        try:
            return datetime.strptime(row[0], TIME_FORMAT)
        except:
            return None
    return None


'''
- If a row with the same Time already exists --> UPDATE it
- Otherwise --> INSERT it
'''
def insert_rows(conn, rows):
    """Insert or update rows based on primary key Time."""
    sql = """
    INSERT INTO ticket_log_table (Time, Name, Note, Project_Name, Requester)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(Time) DO UPDATE SET
        Name = excluded.Name,
        Note = excluded.Note,
        Project_Name = excluded.Project_Name,
        Requester = excluded.Requester;
    """
    cur = conn.cursor()
    cur.executemany(sql, rows)
    conn.commit()
    return len(rows)


'''
- Copy folder log --> Destination: where storage the script
'''
def copy_log_folder(path_a, path_b):
    src = Path(path_a) / "log"
    dest = Path(path_b) / "log"

    if not src.exists():
        raise FileNotFoundError(f"Source folder not found: {src}")

    # Remove destination log folder if exists
    if dest.exists():
        shutil.rmtree(dest)

    # Copy entire folder
    shutil.copytree(src, dest)

    print(f"Copied log folder:\n  from: {src}\n  to:   {dest}")

# ----------------------- Main Logic -----------------------

def run_ingest():
    conn = sqlite3.connect(DB_PATH)
    ensure_table(conn)

    last_time = get_last_time_from_db(conn)

    log_dir = Path(LOG_DIR)
    excel_files = []

    # Select files after last_time
    for file in log_dir.glob("*.xlsx"):
        file_dt = get_excel_file_date(file.name)
        if not file_dt:
            continue

        if last_time is None:
            excel_files.append((file, file_dt))
        else:
            if file_dt > last_time:   # strictly greater
                excel_files.append((file, file_dt))

    all_rows = []

    for path, file_dt in sorted(excel_files, key=lambda x: x[1]):
        df = pd.read_excel(path, engine="openpyxl", dtype=str)

        # Ensure the 5 columns exist
        for col in ["Name", "Time", "Note", "Project_Name", "Requester"]:
            if col not in df.columns:
                df[col] = None

        for _, row in df.iterrows():
            time_dt = parse_time(row["Time"])
            if time_dt is None:
                continue

            record = (
                time_dt.strftime(TIME_FORMAT),  # Time (PRIMARY KEY)
                row["Name"],
                row["Note"],
                row["Project_Name"],
                row["Requester"]
            )
            all_rows.append(record)

    # Deduplicate by 5 fields
    unique_rows = list({r: None for r in all_rows}.keys())

    # Insert into DB
    affected = insert_rows(conn, unique_rows)
    conn.close()

    return {
        "excel_files_opened": len(excel_files),
        "rows_loaded": len(all_rows),
        "rows_after_dedup": len(unique_rows),
        "rows_written_to_db": affected,
        "last_time_before": last_time.strftime(TIME_FORMAT) if last_time else None,
    }

