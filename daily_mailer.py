import os
import smtplib
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from pymongo import MongoClient
from urllib.parse import quote_plus
import pytz

# --- CONFIGURATION ---
MONGO_USER = os.environ.get("MONGO_USER")
MONGO_PASS = os.environ.get("MONGO_PASS")
MONGO_URL = os.environ.get("MONGO_URL")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASS = os.environ.get("SENDER_PASS")

# --- UPDATE RECIPIENTS HERE ---
# Add as many emails as you want, separated by commas
RECIPIENT_LIST = [
    "akashdip.saha@jute-india.com",
    "officialakashdip.333@gmail.com",
    "payal.sinha@jute-india.com,
    "rishavkajaria@gmail.com",
    "raghav@jute-india.com",
    "skajaria@jute-india.com",
] 

def get_ist_time():
    ist_tz = pytz.timezone('Asia/Kolkata')
    return datetime.datetime.now(ist_tz)

def connect_mongo():
    try:
        escaped_user = quote_plus(MONGO_USER)
        escaped_pass = quote_plus(MONGO_PASS)
        connection_string = f"mongodb+srv://{escaped_user}:{escaped_pass}@{MONGO_URL}"
        client = MongoClient(connection_string)
        return client["ocr_project"]
    except Exception as e:
        print(f"MongoDB Connection Error: {e}")
        return None

def send_daily_email():
    print("Starting Daily Emailer...")
    db = connect_mongo()
    if db is None: return

    col = db["daily_pdf_storage"]
    today_str = get_ist_time().strftime("%Y-%m-%d")
    display_date = get_ist_time().strftime("%d %B, %Y") # e.g., 19 November, 2025
    
    # Find reports for today
    cursor = col.find({"upload_date": today_str})
    reports = list(cursor)
    
    if not reports:
        print("No reports found for today. Skipping.")
        return

    # --- LOGIC CHANGE: Get only the LAST (most recent) report ---
    latest_report = reports[-1]

    # --- EMAIL SETUP ---
    msg = MIMEMultipart()
    msg['From'] = f"Jute Reporting System <{SENDER_EMAIL}>"
    # This joins all emails with a comma for the "To" header display
    msg['To'] = ", ".join(RECIPIENT_LIST)
    msg['Subject'] = f"Daily Jute Sauda Report - {display_date}"

    body = f"""
    <html>
    <body style="margin:0; padding:0; background:#f5f7fa; font-family:Arial, sans-serif;">

    <table width="100%" cellspacing="0" cellpadding="0" style="background:#f5f7fa; padding:30px 0;">
      <tr>
        <td align="center">

          <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff; border-radius:10px; box-shadow:0px 2px 10px rgba(0,0,0,0.05); overflow:hidden;">

            <tr>
              <td style="background:linear-gradient(90deg, #0f8364, #1ba57c); padding:22px 28px; color:#ffffff;">
                <h2 style="margin:0; font-size:22px; font-weight:600;">Daily Sauda Report</h2>
                <p style="margin:5px 0 0; font-size:13px; opacity:0.9;">{display_date}</p>
              </td>
            </tr>

            <tr>
              <td style="padding:28px; color:#333333; font-size:14px; line-height:1.6;">

                <p><strong>Dear Sir/Madam,</strong></p>

                <p>Please find attached the latest processed <strong>Jute Sauda Report</strong> for today.  
                The document includes the OCR-extracted details submitted through the reporting system.</p>

                <div style="background:#f7faf9; border:1px solid #d9e7e2; padding:14px 16px; border-radius:8px; margin:20px 0;">
                  <p style="margin:0;"><strong>📄 Report:</strong> Latest file</p>
                  <p style="margin:4px 0 0;"><strong>📅 Date:</strong> {display_date}</p>
                  <p style="margin:4px 0 0;"><strong>✔ Status:</strong> Successfully processed</p>
                </div>

                <br>
                <p style="margin:0; font-weight:600; color:#0f5c47;">Intelligent Jute OCR Automation</p>
                <p style="margin:3px 0 0; font-size:12px; color:#777;">Shaktigarh Textile & Industries LTD.</p>

              </td>
            </tr>

            <tr>
              <td style="background:#f1f3f5; text-align:center; padding:15px; font-size:12px; color:#8a8a8a;">
                This is an automated message. Please do not reply.<br>
                © 2025 - AKS. All rights reserved.
              </td>
            </tr>

          </table>

        </td>
      </tr>
    </table>

    </body>
    </html>
    """
    
    msg.attach(MIMEText(body, 'html'))

    # Attach ONLY the latest file
    try:
        pdf_bytes = latest_report["pdf_data"]
        # Use filename from DB or fallback
        filename = latest_report.get("filename", f"Sauda_Report_{today_str}.pdf")
        
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_bytes)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {filename}")
        msg.attach(part)
        print(f"Attached latest report: {filename}")
    except Exception as e:
        print(f"Error attaching file: {e}")

    # Send
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASS)
        # The server.sendmail function takes the LIST of recipients to send to all of them
        server.sendmail(SENDER_EMAIL, RECIPIENT_LIST, msg.as_string())
        server.quit()
        print("✅ Professional Email sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

if __name__ == "__main__":
    send_daily_email()







