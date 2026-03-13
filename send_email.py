import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
load_dotenv()

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
APP_PASSWORD = os.getenv("APP_PASSWORD")

# --- HÀM GỬI EMAIL CẢNH BÁO ---
def send_overdue_email(overdue_df):
    # Bạn thay bằng email hệ thống và App Password của bạn nhé
    SENDER_EMAIL = os.getenv("SENDER_EMAIL")
    APP_PASSWORD = os.getenv("APP_PASSWORD")
    
    # Danh sách người nhận theo yêu cầu
    # RECEIVERS = ["ying@3v3.ai", "michelle@3v3.ai", "teckwei@3v3.ai", "conan@3v3.ai"]
    RECEIVERS = ["npphuong210@gmail.com"]

    # Chuyển DataFrame những người trễ hạn thành bảng HTML cho đẹp
    html_table = overdue_df[['Company Registered Name', 'Accounting Closing Deadline', 'Days Left', 'Book Keeping Status']].to_html(index=False, border=1, justify='center')

    # Xây dựng nội dung Email
    msg = MIMEMultipart()
    msg['Subject'] = "🚨 ACTION REQUIRED: Overdue Accounting Clients"
    msg['From'] = SENDER_EMAIL
    msg['To'] = ", ".join(RECEIVERS)

    html_body = f"""
    <html>
        <body>
        <p>Hi Ying, Michelle, Teck Wei, and Conan,</p>
        <p>Please be informed that the following clients have passed their Accounting Closing Deadline and their accounts are not yet marked as 'Closing Done':</p>
        {html_table}
        <br>
        <p>Please check the LIVE Dashboard for more details.</p>
        <p><em>This is an automated message from the 3V3 Workflow System.</em></p>
        </body>
    </html>
    """
    msg.attach(MIMEText(html_body, 'html'))

    # Thực hiện gửi
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        return str(e)