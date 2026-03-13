import pandas as pd
from datetime import datetime
import calendar

# --- HÀM THÔNG MINH XỬ LÝ FINANCIAL YEAR END ---
def parse_mixed_fye(date_str):
    date_str = str(date_str).strip()
    if not date_str or date_str.lower() in ['nan', 'none', 'nat', '']:
        return pd.NaT
    
    # 1. Thử đọc ngày đầy đủ (VD: "31 Dec 2025", "31 March 2026")
    try:
        return pd.to_datetime(date_str, dayfirst=True)
    except:
        pass
    
    # 2. Xử lý trường hợp chỉ có mỗi chữ tháng (VD: "September", "March")
    try:
        # Cắt lấy 3 chữ cái đầu để xác định tháng (VD: "September" -> "Sep")
        month_abbr = date_str[:3].title()
        month_num = datetime.strptime(month_abbr, '%b').month
        
        today = datetime.now()
        
        # Xác định năm: Tìm tháng đó ở quá khứ gần nhất (vì Ying chỉ lấy việc đã qua)
        if month_num > today.month:
            year = today.year - 1
        else:
            year = today.year
            
        # Tự động lấy ngày cuối cùng của tháng đó (VD: 30 cho tháng 9, 31 cho tháng 1)
        last_day = calendar.monthrange(year, month_num)[1]
        
        return pd.Timestamp(year=year, month=month_num, day=last_day)
    except:
        return pd.NaT


def filter_dashboard_data(df: pd.DataFrame) -> pd.DataFrame:
    col_service = "Services with ET Management"
    col_fye = "Financial Year End"
    
    # 1. Dọn dẹp cột dịch vụ
    df[col_service] = df[col_service].fillna("").astype(str)
    
    # 2. ĐIỀU KIỆN 1: Loại dịch vụ
    allowed_services = [
        "GST - Jan/Apr/Jul/Oct", "GST - Feb/May/Aug/Nov", "GST - Mar/Jun/Sep/Dec",
        "GST", "Accts - Daily", "Accts - Weekly", "Accts - Monthly", 
        "Accts - Qtrly", "Accounting"
    ]
    
    pattern_allowed = '|'.join(allowed_services)
    has_valid_service = df[col_service].str.contains(pattern_allowed, case=False, regex=True)
    has_invalid_service = df[col_service].str.contains("Annual|Ad Hoc", case=False, regex=True)
    service_mask = has_valid_service & (~has_invalid_service)
    
    # 3. ĐIỀU KIỆN 2: FYE <= Today (Dùng hàm thông minh ở trên)
    # Áp dụng hàm parse_mixed_fye cho từng dòng trong cột FYE
    df["FYE_parsed"] = df[col_fye].apply(parse_mixed_fye)
    
    today = pd.Timestamp(datetime.now().date())
    timeline_mask = (df["FYE_parsed"].notna()) & (df["FYE_parsed"] <= today)
    
    # KẾT HỢP
    filtered_df = df[service_mask & timeline_mask].copy()
    
    # 4. TÍNH DEADLINE: FYE + 3 tháng
    filtered_df["Accounting Closing Deadline"] = filtered_df["FYE_parsed"] + pd.DateOffset(months=3)
    
    return filtered_df