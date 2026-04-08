# ============================================================================
# FILE NAME     : cfg.py
# AUTHOR        : DONG XUAN HIEN
# DIVISION      : SDG2 - KVHS (Kefico Vietnam Hanoi Software)
# DESCRIPTION   : import lib, define global variable
# HISTORY       : 09/03/2026
# ============================================================================

import os
import sqlite3
from pathlib import Path
from datetime import datetime
import pandas as pd
import re
import shutil

LOG_DIR = "./log" 
DB_PATH = "./ticket_log.db" 

DATE_FILE_RE = re.compile(r"(\d{4})_(\d{2})_(\d{2})\.xlsx")
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"   # store in DB

path_a = r"D:\10. Personal\20. Application Python\00. JIRA Download Automation\01. Save Log to Database\temp"
path_b = r"C:\Users\42024014\Downloads\Temp\Office Task\JIRA Download Tool\01. Save Log to Database\version1"
