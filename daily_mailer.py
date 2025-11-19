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
    
    # --- MODERN + GREEN SHIMMER HTML BODY ---
    # Note: CSS animations are not supported in all email clients; a static green gradient
    # fallback is provided for maximum compatibility.
    body = f"""
    <html>
    <head>
      <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
      <style>
        /* Generic resets */
        body {{ margin:0; padding:0; background:#f6f7fb; -webkit-font-smoothing:antialiased; }}
        .wrapper {{ width:100%; padding:30px 0; }}
        .container {{
          width: 100%;
          max-width: 680px;
          margin: 0 auto;
          background: #ffffff;
          border-radius: 12px;
          box-shadow: 0 6px 24px rgba(10,20,30,0.08);
          overflow: hidden;
          font-family: "Helvetica Neue", Arial, sans-serif;
          color: #222;
        }}

        /* Header with green shimmer */
        .header {{
          position: relative;
          padding: 28px 22px;
          text-align: left;
          color: #ffffff;
          background: linear-gradient(90deg, #0f7a63 0%, #0f7a63 100%);
        }}
        /* shimmer overlay - animated */
        .shimmer {{
          position: absolute;
          top: 0;
          left: -50%;
          width: 200%;
          height: 100%;
          background: linear-gradient(120deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.28) 50%, rgba(255,255,255,0.06) 100%);
          transform: skewX(-20deg);
          animation: shimmer 6s linear infinite;
          pointer-events: none;
          opacity: 0.9;
        }}
        @keyframes shimmer {{
          0% {{ transform: translateX(-100%) skewX(-20deg); }}
          50% {{ transform: translateX(0%) skewX(-20deg); }}
          100% {{ transform: translateX(100%) skewX(-20deg); }}
        }}

        /* header text */
        .title {{ font-size: 22px; margin:0 0 6px; letter-spacing:0.2px; }}
        .sub {{ margin:0; font-size:13px; opacity:0.95; }}

        /* content */
        .content {{ padding: 24px; line-height:1.5; color:#333; }}
        .gcard {{
          background: linear-gradient(180deg, #fbfffd 0%, #f4f9f7 100%);
          border-radius: 10px;
          padding: 14px;
          border: 1px solid rgba(7, 96, 77, 0.06);
          box-shadow: 0 2px 8px rgba(6, 45, 36, 0.03);
          margin: 14px 0;
        }}
        .meta-row {{ display:flex; gap:14px; flex-wrap:wrap; font-size:13px; color:#2b4d44; }}
        .meta-item {{ background: rgba(7,96,77,0.06); padding:8px 10px; border-radius:8px; }}

        /* CTA / name */
        .signature {{ margin-top:18px; color:#0b3f35; font-weight:600; }}
        .org {{ font-size:12px; color:#777; margin-top:4px; }}

        /* footer */
        .footer {{ padding:14px; background:#fbfbfb; text-align:center; color:#9aa0a6; font-size:12px; }}

        /* Responsive */
        @media only screen and (max-width:480px) {{
          .container {{ border-radius:8px; }}
          .title {{ font-size:18px; }}
        }}
      </style>
    </head>
    <body>
      <div class="wrapper">
        <div class="container" role="article" aria-label="Daily Sauda Report">
          
          <div class="header" style="background: linear-gradient(90deg, #0f7a63 0%, #2bb58a 100%);">
            <div class="shimmer" aria-hidden="true"></div>
            <div style="position:relative; z-index:2;">
              <h1 class="title">Daily Sauda Report</h1>
              <p class="sub">{display_date}</p>
            </div>
          </div>

          <div class="content">
            <p><strong>Dear Sir / Madam,</strong></p>

            <p>Please find attached the consolidated Jute Sauda Report generated today. We have attached the <strong>latest</strong> processed PDF for your review.</p>

            <div class="gcard" role="group" aria-label="Report summary">
              <div class="meta-row">
                <div class="meta-item">📄 <strong>Report</strong>: Latest</div>
                <div class="meta-item">📅 <strong>Date</strong>: {display_date}</div>
                <div class="meta-item">✅ <strong>Status</strong>: Processed</div>
              </div>

              <p style="margin-top:12px; color:#395349; font-size:14px;">
                This document contains OCR-extracted data from the handwritten ledgers submitted via the OCR app. Please review and let us know if any corrections are required.
              </p>
            </div>

            <p class="signature">Intelligent Jute OCR Automation</p>
            <p class="org">Shaktigarh Textile &amp; Industries LTD.</p>

            <hr style="border:none; height:1px; background: linear-gradient(90deg, rgba(7,96,77,0.06), rgba(0,0,0,0)); margin:18px 0;" />

            <p style="font-size:13px; color:#4a4a4a; margin-bottom:0;">
              If you need a different format or additional reports, reply to this email or contact the automation team.
            </p>
          </div>

          <div class="footer">
            This is an automated email. Please do not reply directly to this message. &nbsp;|&nbsp; © 2025 - AKS. All rights reserved.
          </div>
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
