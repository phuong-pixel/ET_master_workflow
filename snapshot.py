import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from streamlit_autorefresh import st_autorefresh
from tools.filter_dashboard import filter_dashboard_data

# --- CẤU HÌNH ---
SERVICE_ACCOUNT_FILE = "service_account.json"
SHEET_ID = "17khaqN0_TuGPR4uC2GWWq3iPIz-ZKyPSSmD8Rxidvyo"
WORKSHEET_NAME = "Copy of FYE"

st.set_page_config(page_title="3V3 LIVE Monitor", layout="wide")
st_autorefresh(interval=5000, key="datarefresh")

# --- CSS TÙY CHỈNH CHO VÒNG TRÒN ---
st.markdown("""
<style>
    .bubble-container {
        display: flex;
        justify-content: space-around;
        align-items: center;
        text-align: center;
        padding: 20px;
    }
    .bubble {
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        color: black;
        font-weight: bold;
        margin: 10px;
        transition: all 0.5s ease;
        border: 1px solid #999;
    }
    .status-label { font-size: 14px; margin-bottom: 5px; color: #555; }
    .status-value { font-size: 24px; }
    
    /* Màu sắc */
    .bg-not-started { background-color: #e0e0e0; } /* Xám */
    .bg-in-progress { background-color: #4a86e8; }  /* Xanh dương */
    .bg-roadblock { background-color: #ff0000; }    /* Đỏ */
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=10)
def load_data():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
    client = gspread.authorize(creds)
    sh = client.open_by_key(SHEET_ID)
    df = pd.DataFrame(sh.worksheet(WORKSHEET_NAME).get_all_records())
    df.columns = df.columns.str.strip() # Dọn dẹp tên cột
    return df

def calculate_size(value, min_val=0, max_val=100):
    # Tính toán kích thước vòng tròn từ 60px đến 150px dựa trên giá trị
    base_size = 70
    if value == 0: return base_size
    scaling = (value / (max_val if max_val > 0 else 1)) * 80
    return min(150, base_size + scaling)

def render_bubbles(title, df, col_name):
    counts = df[col_name].value_counts()
    ns = int(counts.get("Not Started", 0))
    ip = int(counts.get("In Progress", 0))
    rb = int(counts.get("Roadblock", 0))
    
    max_val = max(ns, ip, rb, 1) # Để lấy tỷ lệ
    
    st.markdown(f"### {title}")
    
    html = f"""
    <div class="bubble-container">
        <div>
            <div class="status-label">Not Started</div>
            <div class="bubble bg-not-started" style="width:{calculate_size(ns, 0, max_val)}px; height:{calculate_size(ns, 0, max_val)}px;">
                <span class="status-value">{ns}</span>
            </div>
        </div>
        <div>
            <div class="status-label">In Progress</div>
            <div class="bubble bg-in-progress" style="width:{calculate_size(ip, 0, max_val)}px; height:{calculate_size(ip, 0, max_val)}px;">
                <span class="status-value">{ip}</span>
            </div>
        </div>
        <div>
            <div class="status-label">Roadblock</div>
            <div class="bubble bg-roadblock" style="width:{calculate_size(rb, 0, max_val)}px; height:{calculate_size(rb, 0, max_val)}px;">
                <span class="status-value">{rb}</span>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

STATUS_COLS = ["Book Keeping Status", "FRS Status", "AGM Status"]
TARGET_STATUSES = ["Not Started", "In Progress", "Roadblock"]

def count_statuses_across_3_cols(df, status_cols=STATUS_COLS):
    # Chuẩn hóa dữ liệu để tránh lệch do khoảng trắng/NaN
    normalized = (
        df[status_cols]
        .apply(lambda s: s.fillna("").astype(str).str.strip())
    )

    all_statuses = normalized.stack()  # gom 3 cột thành 1 cột
    counts = all_statuses.value_counts()

    return {
        "Not Started": int(counts.get("Not Started", 0)),
        "In Progress": int(counts.get("In Progress", 0)),
        "Roadblock": int(counts.get("Roadblock", 0)),
    }

def render_bubbles_from_counts(title, counts):
    ns = counts["Not Started"]
    ip = counts["In Progress"]
    rb = counts["Roadblock"]

    max_val = max(ns, ip, rb, 1)

    st.markdown(f"### {title}")
    html = f"""
    <div class="bubble-container">
        <div>
            <div class="status-label">Not Started</div>
            <div class="bubble bg-not-started" style="width:{calculate_size(ns, 0, max_val)}px; height:{calculate_size(ns, 0, max_val)}px;">
                <span class="status-value">{ns}</span>
            </div>
        </div>
        <div>
            <div class="status-label">In Progress</div>
            <div class="bubble bg-in-progress" style="width:{calculate_size(ip, 0, max_val)}px; height:{calculate_size(ip, 0, max_val)}px;">
                <span class="status-value">{ip}</span>
            </div>
        </div>
        <div>
            <div class="status-label">Roadblock</div>
            <div class="bubble bg-roadblock" style="width:{calculate_size(rb, 0, max_val)}px; height:{calculate_size(rb, 0, max_val)}px;">
                <span class="status-value">{rb}</span>
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# --- THỰC THI ---
st.title("🔴 LIVE Snapshot - workflow.3v3.ai")

try:
    df = load_data()
    df_filtered = filter_dashboard_data(df.copy())
    
    # Task 2: Bong bóng (3 cụm)
    counts_3cols = count_statuses_across_3_cols(df_filtered)
    render_bubbles_from_counts("Overall Status (Book Keeping + FRS + AGM)", counts_3cols)
    
    st.divider()
    
    # Task 1: Bảng Snapshot
    st.subheader("📋 Daily Clients To Be Done")
    
    # Logic ngày tháng (Sửa lỗi 'September' đồ á)
    df_filtered['FYE_Date'] = pd.to_datetime(df_filtered['Financial Year End'], errors='coerce') 
    df_filtered['Deadline'] = df_filtered['FYE_Date'] + timedelta(days=90)
    df_filtered['Days Left'] = (df_filtered['Deadline'] - pd.Timestamp.now().normalize()).dt.days
    
    todo_df = df_filtered[df_filtered['Book Keeping Status'] != 'Closing Done'].sort_values('Days Left')

    def style_rows(row):
        is_audit = "Audit" in str(row['Services with ET Management'])
        return ['background-color: #ffcccc; color: red; font-weight: bold;' if is_audit else '' for _ in row]

    st.dataframe(
        todo_df[['UEN (Unique Entity Number)', 'Company Registered Name', 'Deadline', 'Days Left', 'Book Keeping Status', 'Services with ET Management']].style.apply(style_rows, axis=1),
        width='stretch', hide_index=True
    )

    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

except Exception as e:
    st.error(f"Error: {e}")