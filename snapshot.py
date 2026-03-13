import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from tools.filter_dashboard import filter_dashboard_data
from send_email import send_overdue_email

# --- CẤU HÌNH ---
SERVICE_ACCOUNT_FILE = "service_account.json"
SHEET_ID = "17khaqN0_TuGPR4uC2GWWq3iPIz-ZKyPSSmD8Rxidvyo"
WORKSHEET_NAME = "Copy of FYE"

st.set_page_config(page_title="3V3 LIVE Monitor", layout="wide")
st_autorefresh(interval=5000, key="datarefresh")

# --- CSS TÙY CHỈNH ---
st.markdown("""
<style>
    .bubble-container { display: flex; justify-content: space-around; align-items: center; text-align: center; padding: 20px; }
    .bubble { border-radius: 50%; display: flex; flex-direction: column; justify-content: center; align-items: center; color: black; font-weight: bold; margin: 10px; transition: all 0.5s ease; border: 1px solid #999; }
    .status-label { font-size: 14px; margin-bottom: 5px; color: #555; }
    .status-value { font-size: 32px; }
    .bg-not-started { background-color: #e0e0e0; }
    .bg-in-progress { background-color: #4a86e8; }
    .bg-roadblock { background-color: #ff0000; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=10)
def load_data():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scope)
    client = gspread.authorize(creds)
    sh = client.open_by_key(SHEET_ID)
    df = pd.DataFrame(sh.worksheet(WORKSHEET_NAME).get_all_records())
    df.columns = df.columns.str.strip()
    return df

def calculate_size(value, min_val=0, max_val=100):
    base_size = 70
    if value == 0: return base_size
    scaling = (value / (max_val if max_val > 0 else 1)) * 80
    return min(150, base_size + scaling)

def render_bubbles(title, df, col_name):
    # Dọn dẹp khoảng trắng dư thừa trong Google Sheets để đếm không bị trượt
    df[col_name] = df[col_name].astype(str).str.strip()
    counts = df[col_name].value_counts()
    
    ns = int(counts.get("Not Started", 0))
    ip = int(counts.get("In Progress", 0))
    rb = int(counts.get("Roadblock", 0))
    
    max_val = max(ns, ip, rb, 1)
    
    st.markdown(f"### {title}")
    html = f"""
    <div class="bubble-container">
        <div><div class="status-label">Not Started</div><div class="bubble bg-not-started" style="width:{calculate_size(ns, 0, max_val)}px; height:{calculate_size(ns, 0, max_val)}px;"><span class="status-value">{ns}</span></div></div>
        <div><div class="status-label">In Progress</div><div class="bubble bg-in-progress" style="width:{calculate_size(ip, 0, max_val)}px; height:{calculate_size(ip, 0, max_val)}px;"><span class="status-value">{ip}</span></div></div>
        <div><div class="status-label">Roadblock</div><div class="bubble bg-roadblock" style="width:{calculate_size(rb, 0, max_val)}px; height:{calculate_size(rb, 0, max_val)}px;"><span class="status-value">{rb}</span></div></div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# --- THỰC THI ---
st.title("🔴 LIVE Snapshot - workflow.3v3.ai")

try:
    df = load_data()
    df_filtered = filter_dashboard_data(df.copy())
    
    col1, col2, col3 = st.columns(3)
    with col1: render_bubbles("Book Keeping", df, "Book Keeping Status")
    with col2: render_bubbles("FRS Status", df, "FRS Status")
    with col3: render_bubbles("AGM Status", df, "AGM Status")
    
    st.divider()
    
    st.subheader("📋 Daily Clients To Be Done")
    
    # 1. Tính toán Days Left
    today = pd.Timestamp.now().normalize()
    df_filtered['Days Left'] = (df_filtered['Accounting Closing Deadline'] - today).dt.days
    
    # 2. Tạo cột phụ chứa "Tháng Năm" (VD: December 2025) để đưa vào bộ lọc
    # Dùng %B để ra chữ Tháng đầy đủ giống Google Sheets (January, December...)
    df_filtered['FYE Filter'] = df_filtered['FYE_parsed'].dt.strftime('%B %Y')
    df_filtered['Deadline Filter'] = df_filtered['Accounting Closing Deadline'].dt.strftime('%B %Y')
    
    # 3. Lọc trạng thái chưa đóng sổ
    df_filtered['Book Keeping Status'] = df_filtered['Book Keeping Status'].astype(str).str.strip()
    todo_df = df_filtered[df_filtered['Book Keeping Status'] != 'Closing Done'].sort_values('Days Left')

    # --- BỘ LỌC MULTISELECT (GIỐNG GOOGLE SHEETS) ---
    st.markdown("##### 🔍 Filter")
    filter_col1, filter_col2 = st.columns(2)
    
    with filter_col1:
        # Lấy danh sách các tháng hiện có (bỏ các ô trống)
        fye_options = sorted(todo_df['FYE Filter'].dropna().unique().tolist())
        selected_fye = st.multiselect("Filter Financial Year End:", fye_options, placeholder="Select month...")
        
    with filter_col2:
        deadline_options = sorted(todo_df['Deadline Filter'].dropna().unique().tolist())
        selected_deadline = st.multiselect("Filter Accounting Closing Deadline:", deadline_options, placeholder="Select month...")

    # --- ÁP DỤNG BỘ LỌC NẾU NGƯỜI DÙNG CÓ CHỌN ---
    if selected_fye:
        todo_df = todo_df[todo_df['FYE Filter'].isin(selected_fye)]
    if selected_deadline:
        todo_df = todo_df[todo_df['Deadline Filter'].isin(selected_deadline)]

    # 4. Định dạng lại ngày tháng cho đẹp trước khi đưa lên bảng web
    todo_df['Accounting Closing Deadline'] = todo_df['Accounting Closing Deadline'].dt.strftime('%d %b %Y')
    todo_df['Financial Year End'] = todo_df['FYE_parsed'].dt.strftime('%d %b %Y')

    def style_rows(row):
        is_audit = "Audit" in str(row['Services with ET Management'])
        return ['background-color: #ffcccc; color: red; font-weight: bold;' if is_audit else '' for _ in row]

    # Khai báo các cột muốn hiển thị
    display_cols = [
        'UEN (Unique Entity Number)', 
        'Company Registered Name', 
        'Financial Year End',
        'Accounting Closing Deadline', 
        'Days Left', 
        'Book Keeping Status', 
        'Services with ET Management'
    ]
    
    st.dataframe(
        todo_df[display_cols].style.apply(style_rows, axis=1),
        width='stretch', 
        hide_index=True
    )

    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

    st.divider()
    st.markdown("##### 🚨 Overdue Alert")
    
    # Lọc ra những khách hàng đã trễ hạn (Days Left < 0)
    overdue_clients = todo_df[todo_df['Days Left'] < 0]
    
    if not overdue_clients.empty:
        st.error(f"Found {len(overdue_clients)} clients that are overdue for closing!")
        
        # Nút bấm gửi email
        if st.button("📧 Send Email Report to Management"):
            with st.spinner("Sending email..."):
                result = send_overdue_email(overdue_clients)
                if result is True:
                    st.success("Email sent successfully to Ying, Michelle, Teck Wei and Conan!")
                else:
                    st.error(f"Error sending email: {result}")
    else:
        st.success("Great! No clients are overdue for closing.")

    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

except Exception as e:
    st.error(f"Error: {e}")