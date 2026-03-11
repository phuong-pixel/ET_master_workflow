import pandas as pd
from datetime import datetime

def filter_dashboard_data(df: pd.DataFrame) -> pd.DataFrame:
    # --- ĐIỀU KIỆN 1: Loại dịch vụ (Service Type) ---
    # Chỉ giữ các dịch vụ trong danh sách cho phép
    allowed_services = [
        "GST - Jan/Apr/Jul/Oct",
        "GST - Feb/May/Aug/Nov",
        "GST - Mar/Jun/Sep/Dec",
        "GST",
        "Accts - Daily", 
        "Accts - Weekly", 
        "Accts - Monthly", 
        "Accts - Qtrly"
    ]
    
    # Giả sử tên cột dịch vụ là "Service Type"
    service_mask = df["Service Type"].isin(allowed_services)
    
    # --- ĐIỀU KIỆN 2: Thời điểm hiển thị (FYE <= Today) ---
    # 1. Chuyển đổi cột FYE sang định dạng datetime (nếu chưa có)
    # Lưu ý: Cần đảm bảo cột này chứa thông tin ngày tháng năm đầy đủ
    df["FYE_parsed"] = pd.to_datetime(df["FYE"], errors="coerce", dayfirst=True)
    
    # 2. Lấy ngày hôm nay
    today = pd.Timestamp(datetime.now().date())
    
    # 3. Tạo mask lọc: FYE phải nhỏ hơn hoặc bằng hôm nay và không được NaT (lỗi parse)
    timeline_mask = (df["FYE_parsed"].notna()) & (df["FYE_parsed"] <= today)
    
    # --- KẾT HỢP CẢ 2 ĐIỀU KIỆN ---
    filtered_df = df[service_mask & timeline_mask].copy()
    
    # Dọn dẹp: Xóa cột phụ nếu không cần dùng nữa
    # filtered_df = filtered_df.drop(columns=["FYE_parsed"])
    
    return filtered_df

# Ví dụ áp dụng:
# df_final = filter_dashboard_data(df_input)