import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

# ===== CONFIG =====
SERVICE_ACCOUNT_FILE = "service_account.json"
SHEET_ID = "17khaqN0_TuGPR4uC2GWWq3iPIz-ZKyPSSmD8Rxidvyo"
WORKSHEET_NAME = "FYE 1"

SOURCE_FILE = "New Client Database.xlsx"

UEN_COL = "UEN (Unique Entity Number)"

# Cột cần update khi UEN đã tồn tại
COLUMNS_TO_UPDATE = [
    "Financial Year End",
    "Services with ET Management"
]

# Cột cho dòng mới khi UEN chưa tồn tại
COLUMNS_FOR_NEW_ROW = [
    "UEN (Unique Entity Number)",
    "Company Registered Name",
    "Financial Year End",
    "Services with ET Management"
]

# ==================

# Auth
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=scope
)

client = gspread.authorize(creds)

# Load Google Sheet
sheet = client.open_by_key(SHEET_ID)
worksheet = sheet.worksheet(WORKSHEET_NAME)

# Lấy toàn bộ dữ liệu từ Google Sheet
all_values = worksheet.get_all_values()
headers = all_values[0]
rows = all_values[1:]

# Load source Excel
df_source = pd.read_excel(SOURCE_FILE)
df_source = df_source.drop_duplicates(subset=UEN_COL, keep="last")
df_source.set_index(UEN_COL, inplace=True)

# Tìm vị trí cột trong Google Sheet
uen_col_idx = headers.index(UEN_COL)
col_indices = {col: headers.index(col) for col in COLUMNS_TO_UPDATE}

# Tập hợp các UEN đã có trong Google Sheet
existing_uens = set(row[uen_col_idx] for row in rows)

# === 1. Update các UEN đã tồn tại ===
cells_to_update = []
for row_idx, row in enumerate(rows, start=2):
    uen_value = row[uen_col_idx]
    if uen_value in df_source.index:
        for col_name, col_idx in col_indices.items():
            new_value = df_source.loc[uen_value, col_name]
            if pd.notna(new_value):
                cells_to_update.append(
                    gspread.Cell(row_idx, col_idx + 1, str(new_value))
                )

if cells_to_update:
    worksheet.update_cells(cells_to_update)
    print(f"✅ Đã cập nhật {len(cells_to_update)} ô")

# === 2. Thêm các UEN mới chưa có ===
new_rows = []
for uen_value in df_source.index:
    if str(uen_value) not in existing_uens:
        # Tạo dòng trống theo đúng số cột của sheet
        new_row = [""] * len(headers)
        for col_name in COLUMNS_FOR_NEW_ROW:
            if col_name in headers:
                col_idx = headers.index(col_name)
                if col_name == UEN_COL:
                    new_row[col_idx] = str(uen_value)
                else:
                    val = df_source.loc[uen_value, col_name]
                    new_row[col_idx] = str(val) if pd.notna(val) else ""
        new_rows.append(new_row)

if new_rows:
    worksheet.append_rows(new_rows, value_input_option="USER_ENTERED")
    print(f"✅ Đã thêm {len(new_rows)} dòng mới")

if not cells_to_update and not new_rows:
    print("⚠️ Không có gì để cập nhật")
else:
    print("🎉 Hoàn tất!")