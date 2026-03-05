import calendar
import pandas as pd

ACCOUNTING_CLOSING_COL = "Accounting Closing Deadline"

MONTH_MAP = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
MONTH_MAP.update({m.lower(): i for i, m in enumerate(calendar.month_abbr) if m})

def calc_accounting_deadline(fye_value: str) -> str:
    if pd.isna(fye_value):
        return ""
    raw = str(fye_value).strip().lower()
    month = MONTH_MAP.get(raw)

    # Fallback if source has date format
    if month is None:
        parsed = pd.to_datetime(raw, errors="coerce", dayfirst=True)
        if pd.isna(parsed):
            return ""
        month = parsed.month

    base = pd.Timestamp(year=2000, month=month, day=1)
    deadline = (base + pd.DateOffset(months=3)) + pd.offsets.MonthEnd(0)
    return deadline.strftime("%d %b")   # example: 31 Oct, 30 Jun