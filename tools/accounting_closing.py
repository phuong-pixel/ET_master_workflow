import calendar
import pandas as pd
from datetime import datetime

ACCOUNTING_CLOSING_COL = "Accounting Closing Deadline"

# Tạo map cho tên tháng
MONTH_MAP = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
MONTH_MAP.update({m.lower(): i for i, m in enumerate(calendar.month_abbr) if m})

def calc_accounting_deadline(fye_value: str) -> str:
    if pd.isna(fye_value) or str(fye_value).strip() == "":
        return ""
    
    raw = str(fye_value).strip().lower()
    month = MONTH_MAP.get(raw)
    today = datetime.now()

    # Trường hợp 1: User chỉ nhập mỗi tên tháng (VD: "December", "Sep")
    if month is not None:
        # Nếu tháng FYE lớn hơn tháng hiện tại -> Đích thị là của năm ngoái
        # Ví dụ: Nay là tháng 3/2026. FYE là tháng 12 -> Phải là 12/2025
        year = today.year - 1 if month > today.month else today.year
        base = pd.Timestamp(year=year, month=month, day=1)

    # Trường hợp 2: User nhập ngày tháng đầy đủ (VD: "31 Dec 2025")
    else:
        parsed = pd.to_datetime(raw, errors="coerce", dayfirst=True)
        if pd.isna(parsed):
            return ""
        # PHẢI GIỮ NGUYÊN NGÀY THÁNG NĂM GỐC CỦA DATA
        base = parsed

    # Cộng thêm 3 tháng và lấy ngày cuối cùng của tháng đó
    deadline = base + pd.DateOffset(months=3) + pd.offsets.MonthEnd(0)
    
    return deadline.strftime("%d %b %Y")

# --- Ví dụ kết quả ---
# print(calc_accounting_deadline("Dec"))     # Kết quả: 31 Mar 2027 (vì hiện tại là 2026)
# print(calc_accounting_deadline("January")) # Kết quả: 30 Apr 2026