import pandas as pd
from datetime import datetime

def filter_dashboard_data(df: pd.DataFrame) -> pd.DataFrame:
    # 1. Khai báo đúng tên cột từ dữ liệu gốc
    col_service = "Services with ET Management"
    col_fye = "Financial Year End"
    
    # 2. ĐIỀU KIỆN 1: Loại dịch vụ
    # Thêm "Accounting" vào danh sách để không bị sót data
    allowed_services = [
        "GST - Jan/Apr/Jul/Oct",
        "GST - Feb/May/Aug/Nov",
        "GST - Mar/Jun/Sep/Dec",
        "GST",
        "Accts - Daily", 
        "Accts - Weekly", 
        "Accts - Monthly", 
        "Accts - Qtrly",
        "Accounting" 
    ]
    
    # Biến danh sách thành một chuỗi regex: "GST|Accts - Daily|Accounting|..."
    # Ký tự '|' có nghĩa là "HOẶC"
    pattern = '|'.join(allowed_services)
    
    # Ép kiểu về string để tránh lỗi nếu có ô bị trống (NaN), sau đó tìm kiếm chuỗi
    df[col_service] = df[col_service].fillna("").astype(str)
    service_mask = df[col_service].str.contains(pattern, case=False, regex=True)
    
    # 3. ĐIỀU KIỆN 2: Thời điểm hiển thị (FYE <= Today)
    df["FYE_parsed"] = pd.to_datetime(df[col_fye], errors="coerce", dayfirst=True, format='mixed')
    today = pd.Timestamp(datetime.now().date())
    timeline_mask = (df["FYE_parsed"].notna()) & (df["FYE_parsed"] <= today)
    
    # 4. KẾT HỢP
    filtered_df = df[service_mask & timeline_mask].copy()
    
    return filtered_df