import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

from highlight_red_audit import setup_audit_conditional_formatting

# ===== CONFIG =====
SERVICE_ACCOUNT_FILE = "service_account.json"
SHEET_ID = "17khaqN0_TuGPR4uC2GWWq3iPIz-ZKyPSSmD8Rxidvyo"
WORKSHEET_NAME = "FYE"

SOURCE_SHEET_ID = "18zN1JZf9gz2OALcHODbTuokbcsnVjeKRkV1cyrhom6w"
SOURCE_WORKSHEET_NAME = "Master_DB"

# Key để so sánh: Company Registered Name (không dùng Client ID)
PRIMARY_KEY_COL = "Company Registered Name"
FYE_COL = "Financial Year End"

# Cột cần update khi Company Name đã tồn tại
COLUMNS_TO_UPDATE = [
    "Client ID",
    "UEN (Unique Entity Number)",
    "Financial Year End",  
    "Services with ET Management",
]

# Cột cho dòng mới khi Company Name chưa tồn tại
COLUMNS_FOR_NEW_ROW = [
    "Client ID",
    "UEN (Unique Entity Number)",
    "Company Registered Name",
    "Financial Year End", 
    "Services with ET Management",
    "Engagement Status"
]

# ==================

print("🚀 Client Sync - Single Sheet Mode")
print("=" * 60)

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

required_columns = set(COLUMNS_TO_UPDATE + COLUMNS_FOR_NEW_ROW)
missing_columns = [col for col in required_columns if col not in headers]

if missing_columns:
    print(f"\n🔧 Tạo {len(missing_columns)} cột mới:")
    for col in missing_columns:
        print(f"  • {col}")
    
    # Thêm missing columns vào cuối header
    headers.extend(missing_columns)
    
    # Update header row trong sheet
    worksheet.update('1:1', [headers])
    
    # Reload lại data sau khi thêm header
    all_values = worksheet.get_all_values()
    rows = all_values[1:]
    
    print(f"✅ Đã thêm cột mới vào sheet")

print()

source_sheet = client.open_by_key(SOURCE_SHEET_ID)
source_worksheet = source_sheet.worksheet(SOURCE_WORKSHEET_NAME)
records = source_worksheet.get_all_values()
df_source = pd.DataFrame(records[1:], columns=records[0])

print(f"📊 Tổng số clients trong source: {len(df_source)}")

df_source[FYE_COL] = df_source[FYE_COL].str.strip().str.capitalize()

if "Engagement Status" in df_source.columns:
    before_count = len(df_source)
    df_source = df_source[df_source["Engagement Status"] != "Terminated"].copy()
    terminated_count = before_count - len(df_source)
    if terminated_count > 0:
        print(f"⚠️ Excluded {terminated_count} terminated clients")

# Filter out empty Company Names
df_source = df_source[
    df_source[PRIMARY_KEY_COL].notna() & 
    (df_source[PRIMARY_KEY_COL].str.strip() != '')
].copy()

# Remove duplicates by Company Name, keep last
df_source = df_source.drop_duplicates(subset=PRIMARY_KEY_COL, keep="last")
df_source.set_index(PRIMARY_KEY_COL, inplace=True) 

print(f"📋 Sau khi loại duplicate: {len(df_source)} clients")

# Count by FYE để thấy phân bổ
fye_counts = df_source[FYE_COL].value_counts().sort_index()
print(f"\n📊 Phân bổ theo FYE:")
for fye, count in fye_counts.items():
    print(f"  • {fye}: {count} clients")

print()

# Tìm vị trí cột trong Google Sheet
primary_key_col_idx = headers.index(PRIMARY_KEY_COL)
fye_col_idx = headers.index(FYE_COL)
col_indices = {col: headers.index(col) for col in COLUMNS_TO_UPDATE}

# Tập hợp các Company Names đã có trong Google Sheet
existing_company_names = set(
    row[primary_key_col_idx] for row in rows if row[primary_key_col_idx]
)

# === 1. Update các Company Name đã tồn tại ===
cells_to_update = []
updated_clients = []
fye_changes = {}  # Track FYE changes

for row_idx, row in enumerate(rows, start=2):
    company_name = row[primary_key_col_idx]
    
    if company_name in df_source.index:
        updated_cols = []
        for col_name, col_idx in col_indices.items():
            new_value = df_source.loc[company_name, col_name]
            
            if pd.notna(new_value):
                old_value = row[col_idx] if col_idx < len(row) else ""
                
                if str(new_value) != str(old_value):
                    cells_to_update.append(
                        gspread.Cell(row_idx, col_idx + 1, str(new_value))
                    )
                    updated_cols.append(f"{col_name}: '{old_value}' → '{new_value}'")
                    
                    # Track FYE changes đặc biệt
                    if col_name == FYE_COL:
                        fye_changes[company_name] = (old_value, new_value)
        
        if updated_cols:
            updated_clients.append(f"  • {company_name}:")
            for change in updated_cols:
                updated_clients.append(f"    - {change}")

if cells_to_update:
    worksheet.update_cells(cells_to_update)
    updated_count = len([c for c in updated_clients if c.startswith('  •')])
    print(f"✅ Đã cập nhật {len(cells_to_update)} ô cho {updated_count} clients")
    
    # Highlight audit clients
    # setup_audit_conditional_formatting(worksheet, headers)

    if fye_changes:
        print(f"\n⚠️ FYE Changes (ảnh hưởng đến filter):")
        for company, (old, new) in fye_changes.items():
            print(f"  • {company}: {old} → {new}")
    
    if updated_clients and len(updated_clients) <= 50:  # Chỉ show chi tiết nếu < 50
        print("\n📝 Chi tiết cập nhật:")
        for line in updated_clients:
            print(line)
else:
    print("ℹ️ Không có client nào cần update")

# === 2. Thêm các Company Name mới ===
new_rows = []
new_company_names = []
new_by_fye = {}  # Track new clients by FYE

for company_name in df_source.index:
    if str(company_name) not in existing_company_names:
        new_row = [""] * len(headers)
        fye_value = None
        
        for col_name in COLUMNS_FOR_NEW_ROW:
            if col_name in headers:
                col_idx = headers.index(col_name)
                if col_name == PRIMARY_KEY_COL:
                    new_row[col_idx] = str(company_name)
                else:
                    val = df_source.loc[company_name, col_name]
                    new_row[col_idx] = str(val) if pd.notna(val) else ""
                    
                    if col_name == FYE_COL and pd.notna(val):
                        fye_value = str(val)
        
        new_rows.append(new_row)
        new_company_names.append(company_name)
        
        # Track by FYE
        if fye_value:
            if fye_value not in new_by_fye:
                new_by_fye[fye_value] = []
            new_by_fye[fye_value].append(company_name)

if new_rows:
    worksheet.append_rows(new_rows, value_input_option="USER_ENTERED")
    print(f"\n✅ Đã thêm {len(new_rows)} client mới:")
    
    # Group by FYE
    for fye, companies in sorted(new_by_fye.items()):
        print(f"  📁 {fye}: {len(companies)} clients")
        if len(companies) <= 10:  # Chỉ show chi tiết nếu <= 10
            for company in companies:
                print(f"     - {company}")

    all_values = worksheet.get_all_values()
    rows = all_values[1:]

    start_row = len(rows) - len(new_rows) + 2
    end_row = len(rows) + 1
    # setup_audit_conditional_formatting(worksheet, headers, start_row, end_row)

else:
    print("\nℹ️ Không có client mới")

# === 3. Xóa các client terminated ===
clients_to_delete = []

for row_idx, row in enumerate(rows, start=2):
    company_name = row[primary_key_col_idx]
    
    # Nếu Company Name có trong sheet đích NHƯNG:
    # - Không còn trong source (đã bị filter do terminated)
    # - Hoặc status = "Terminated" trong source
    if company_name and company_name not in df_source.index:
        clients_to_delete.append((row_idx, company_name))

if clients_to_delete:
    # Xóa từ dưới lên để index không bị lệch
    for row_idx, company_name in sorted(clients_to_delete, reverse=True):
        worksheet.delete_rows(row_idx)
    
    print(f"\n🗑️ Đã xóa {len(clients_to_delete)} client terminated:")
    for _, company_name in clients_to_delete[:10]:  # Show max 10
        print(f"  • {company_name}")
else:
    print("\nℹ️ Không có client nào cần xóa")

# === 4. Summary ===
print("\n" + "=" * 60)
if not cells_to_update and not new_rows:
    print("✓ Tất cả dữ liệu đã đồng bộ")
else:
    updated_count = len([c for c in updated_clients if c.startswith('  •')])
    new_count = len(new_rows)
    deleted_count = len(clients_to_delete)
    print(f"🎉 Hoàn tất!")
    print(f"📊 Tổng kết: {updated_count} updated | {new_count} new | {deleted_count} deleted | {updated_count + new_count + deleted_count} total changes")

# Highlight audit clients
setup_audit_conditional_formatting(worksheet, headers)

print("\n💡 Sử dụng Filter View trong Google Sheets để xem từng FYE")
print("   Data → Filter views → Tạo filter theo FYE column")