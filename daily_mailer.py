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
RECIPIENT_LIST = ["akashdip.saha@jute-india.com"] 

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
    msg['To'] = ", ".join(RECIPIENT_LIST)
    msg['Subject'] = f"Daily Jute Sauda Report - {display_date}"
    
    # --- PROFESSIONAL HTML BODY ---
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <div style="max-width: 600px; margin: 0 auto; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">
            
            <div style="background-color: #016B61; color: #ffffff; padding: 20px; text-align: center;">
                <h2 style="margin: 0;">Daily Sauda Report</h2>
                <p style="margin: 5px 0 0; font-size: 14px;">{display_date}</p>
            </div>

            <div style="padding: 25px;">
                <p><strong>Dear Sir/Madam,</strong></p>
                
                <p>Please find attached the consolidated Jute Sauda OCR report generated today.</p>
                
                <div style="background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>📄 Reports Sent:</strong> 1 (Latest)</p>
                    <p style="margin: 0;"><strong>📅 Date:</strong> {display_date}</p>
                    <p style="margin: 0;"><strong>✅ Status:</strong> Successfully Processed</p>
                </div>

                <p>This document contains the digitized data extracted from the handwritten ledgers submitted via the OCR portal.</p>
                
                <br>
                <p>Best Regards,</p>
                <p><strong>Intelligent Jute OCR Automation</strong><br>
                <span style="color: #888; font-size: 12px;">Shaktigarh Textile & Industries LTD.</span></p>
            </div>

            <div style="background-color: #f4f4f4; padding: 15px; text-align: center; font-size: 11px; color: #888;">
                <p style="margin: 0;">This is an automated email. Please do not reply directly to this message.</p>
                <p style="margin: 5px 0 0;">~AKS</p>
            </div>
        </div>
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
        server.sendmail(SENDER_EMAIL, RECIPIENT_LIST, msg.as_string())
        server.quit()
        print("✅ Professional Email sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

if __name__ == "__main__":
    send_daily_email()
