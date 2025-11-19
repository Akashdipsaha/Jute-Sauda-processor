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

# --- CONFIGURATION (Loaded from GitHub Secrets) ---
# We use os.environ so your passwords aren't exposed in the public code file
MONGO_USER = os.environ.get("MONGO_USER")
MONGO_PASS = os.environ.get("MONGO_PASS")
MONGO_URL = os.environ.get("MONGO_URL")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASS = os.environ.get("SENDER_PASS")

# Recipient list - You can edit this list directly here
RECIPIENT_LIST = ["akashdip.saha@jute-india.com"] 

def get_ist_time():
    # IST is UTC + 5:30
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
    if db is None:
        return

    col = db["daily_pdf_storage"]
    
    # Get today's date in IST to match the file upload date
    today_str = get_ist_time().strftime("%Y-%m-%d")
    print(f"Looking for reports uploaded on: {today_str}")
    
    # Find all reports uploaded "Today"
    cursor = col.find({"upload_date": today_str})
    reports = list(cursor)
    
    if not reports:
        print("No reports found for today. Skipping email.")
        return

    print(f"Found {len(reports)} report(s). Preparing email...")

    # Setup Email
    msg = MIMEMultipart()
    msg['From'] = f"Jute Automation <{SENDER_EMAIL}>"
    msg['To'] = ", ".join(RECIPIENT_LIST)
    msg['Subject'] = f"Daily Jute Sauda Reports - {today_str}"
    
    body = f"""
    <html>
      <body>
        <p><strong>Dear Sir/Madam,</strong></p>
        <p>Please find attached the <strong>{len(reports)}</strong> Sauda Report(s) generated today ({today_str}).</p>
        <hr>
        <p style="font-size: 12px; color: #666;">Automated System</p>
      </body>
    </html>
    """
    msg.attach(MIMEText(body, 'html'))

    # Attach every PDF found in DB for today
    for i, doc in enumerate(reports):
        try:
            pdf_bytes = doc["pdf_data"]
            filename = doc.get("filename", f"report_{i}.pdf")
            
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(pdf_bytes)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename= {filename}")
            msg.attach(part)
        except Exception as e:
            print(f"Error attaching file {i}: {e}")

    # Send Email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASS)
        server.sendmail(SENDER_EMAIL, RECIPIENT_LIST, msg.as_string())
        server.quit()
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

if __name__ == "__main__":
    send_daily_email()