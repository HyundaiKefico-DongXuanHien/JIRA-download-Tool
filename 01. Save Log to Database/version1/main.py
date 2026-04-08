# ============================================================================
# FILE NAME     : save_log_to_dtb
# AUTHOR        : DONG XUAN HIEN
# DIVISION      : SDG2 - KVHS (Kefico Vietnam Hanoi Software)
# DESCRIPTION   : parsing all log excel file --> save into dtb
# HISTORY       : 09/03/2026
# ============================================================================

from sub_function import *

if __name__ == "__main__":
    copy_log_folder(path_a, path_b)
    result = run_ingest()
    print(result)