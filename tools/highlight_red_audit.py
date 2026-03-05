def setup_audit_conditional_formatting(worksheet, headers):
    """Setup conditional formatting rule cho AUDIT clients - highlight entire row"""
    
    services_col_idx = headers.index("Services with ET Management")
    # Convert index to column letter (0->A, 1->B, etc.)
    if services_col_idx < 26:
        col_letter = chr(65 + services_col_idx)  # 0->A, 1->B, 2->C...
    else:
        # Handle columns beyond Z (AA, AB, etc.)
        first_letter = chr(64 + (services_col_idx // 26))
        second_letter = chr(65 + (services_col_idx % 26))
        col_letter = first_letter + second_letter
    
    red_format = {
        "backgroundColor": {
            "red": 1.0,
            "green": 0.0,
            "blue": 0.0
        },
        "textFormat": {
            "foregroundColor": {
                "red": 1.0,
                "green": 1.0,
                "blue": 1.0
            },
            "bold": False
        }
    }
    
    # FIX: Dùng REGEXMATCH thay vì SEARCH
    # Case insensitive match cho "Audit"
    formula = f'=REGEXMATCH(${col_letter}2, "(?i)(^|,\s*)Audit($|,)")'
    
    rule = {
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": worksheet.id,
                    "startRowIndex": 1,  # Skip header (row 0)
                    "endRowIndex": 1000,  # Adjust as needed
                    "startColumnIndex": 0,  # Start from column A
                    "endColumnIndex": len(headers)  # To last column
                }],
                "booleanRule": {
                    "condition": {
                        "type": "CUSTOM_FORMULA",
                        "values": [{
                            "userEnteredValue": formula
                        }]
                    },
                    "format": red_format
                }
            },
            "index": 0
        }
    }
    
    body = {"requests": [rule]}
    worksheet.spreadsheet.batch_update(body)
    print(f"🎨 Đã setup conditional formatting: tô đỏ entire row khi có AUDIT")