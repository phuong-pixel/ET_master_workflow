import calendar
import pandas as pd
from datetime import datetime

ACCOUNTING_CLOSING_COL = "Accounting Closing Deadline"

# Tạo map cho tên tháng
MONTH_MAP = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
MONTH_MAP.update({m.lower(): i for i, m in enumerate(calendar.month_abbr) if m})

def calc_accounting_deadline(fye_value: str) -> str:
    if pd.isna(fye_value):
        return ""
    
    raw = str(fye_value).strip().lower()
    month = MONTH_MAP.get(raw)

    # Fallback nếu input là định dạng ngày tháng
    if month is None:
        parsed = pd.to_datetime(raw, errors="coerce", dayfirst=True)
        if pd.isna(parsed):
            return ""
        month = parsed.month

    # Lấy năm hiện tại làm mốc
    current_year = datetime.now().year
    base = pd.Timestamp(year=current_year, month=month, day=1)
    
    # Cộng thêm 3 tháng và lấy ngày cuối cùng của tháng đó
    # Pandas tự động xử lý việc nhảy năm (vd: Dec 2024 -> Mar 2025)
    deadline = (base + pd.DateOffset(months=3)) + pd.offsets.MonthEnd(0)
    
    # Format: %d %b %Y -> 31 Mar 2025
    # Hoặc: %d %b %y -> 31 Mar 25
    return deadline.strftime("%d %b %Y")

# --- Ví dụ kết quả ---
# print(calc_accounting_deadline("Dec"))     # Kết quả: 31 Mar 2027 (vì hiện tại là 2026)
# print(calc_accounting_deadline("January")) # Kết quả: 30 Apr 2026