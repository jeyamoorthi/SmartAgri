import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASS = os.getenv('SMTP_PASS', '')
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))

def _send_email_sync(to_email: str, subject: str, html_body: str) -> bool:
    """Send email synchronously via SMTP."""
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f"SmartAgri 🌾 <{SMTP_USER}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_body, 'html'))
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        print(f"[INFO] Email sent to {to_email}: {subject}")
        return True
    except Exception as e:
        print(f"[WARNING] Email send failed to {to_email}: {e}")
        return False

async def send_email(to_email: str, subject: str, html_body: str):
    import asyncio
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _send_email_sync, to_email, subject, html_body)

async def send_irrigation_reminder(to_email: str, crop: str, schedule_item: dict):
    subject = f"🌊 Irrigation Reminder – {crop} | SmartAgri"
    html = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #FAFAF7; border-radius: 16px; overflow: hidden;">
        <div style="background: linear-gradient(135deg, #2D6A4F, #74C69D); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 24px;">🌊 Irrigation Reminder</h1>
            <p style="color: #E8F5E9; margin-top: 8px;">SmartAgri — Your Farm, Smarter</p>
        </div>
        <div style="padding: 30px;">
            <p style="color: #333; font-size: 16px;">Vanakkam! Your irrigation is scheduled soon:</p>
            <div style="background: #E8F5E9; border-radius: 12px; padding: 20px; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>🌾 Crop:</strong> {crop}</p>
                <p style="margin: 5px 0;"><strong>📅 Day:</strong> {schedule_item.get('day', '')}</p>
                <p style="margin: 5px 0;"><strong>⏰ Time:</strong> {schedule_item.get('time', '')}</p>
                <p style="margin: 5px 0;"><strong>⏱ Duration:</strong> {schedule_item.get('duration_mins', 30)} minutes</p>
                <p style="margin: 5px 0;"><strong>💧 Method:</strong> {schedule_item.get('method', 'Drip')}</p>
            </div>
            <div style="background: #FFF8E1; border-radius: 12px; padding: 15px; margin-top: 15px;">
                <p style="color: #F57F17; font-weight: bold; margin: 0;">💡 Water-Saving Tip</p>
                <p style="color: #666; margin: 5px 0 0 0;">Irrigate early morning (before 7 AM) to reduce evaporation by up to 30%.</p>
            </div>
        </div>
        <div style="background: #2D6A4F; padding: 15px; text-align: center;">
            <p style="color: #74C69D; margin: 0; font-size: 12px;">SmartAgri — AI-Powered Precision Farming 🌱</p>
        </div>
    </div>
    """
    await send_email(to_email, subject, html)

async def send_pest_alert(to_emails: list, pest_name: str, severity: int, location_desc: str, crop: str):
    if severity >= 8:
        severity_text = 'Critical'
        severity_color = '#D32F2F'
    elif severity >= 6:
        severity_text = 'High'
        severity_color = '#F57C00'
    elif severity >= 4:
        severity_text = 'Moderate'
        severity_color = '#FFA000'
    else:
        severity_text = 'Low'
        severity_color = '#388E3C'

    subject = f"⚠️ Pest Alert Near Your Farm – {pest_name} | SmartAgri"
    html = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #FAFAF7; border-radius: 16px; overflow: hidden;">
        <div style="background: linear-gradient(135deg, {severity_color}, #FF5722); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 24px;">⚠️ Pest Alert</h1>
            <p style="color: #FFCDD2; margin-top: 8px;">Reported near your farming area</p>
        </div>
        <div style="padding: 30px;">
            <div style="background: #FFEBEE; border-left: 4px solid {severity_color}; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                <p style="margin: 5px 0;"><strong>🐛 Pest:</strong> {pest_name}</p>
                <p style="margin: 5px 0;"><strong>⚡ Severity:</strong> <span style="color: {severity_color}; font-weight: bold;">{severity_text} ({severity}/10)</span></p>
                <p style="margin: 5px 0;"><strong>🌾 Affected Crop:</strong> {crop}</p>
                <p style="margin: 5px 0;"><strong>📍 Reported Near:</strong> {location_desc}</p>
            </div>
            <div style="background: #E8F5E9; border-radius: 12px; padding: 20px;">
                <p style="color: #2D6A4F; font-weight: bold; margin: 0 0 10px 0;">🛡 Precautionary Steps:</p>
                <ul style="color: #333; padding-left: 20px;">
                    <li>Inspect your {crop} fields immediately</li>
                    <li>Apply neem oil spray (5ml/L) as preventive measure</li>
                    <li>Set up yellow sticky traps around field borders</li>
                    <li>Report any sightings on SmartAgri app</li>
                </ul>
            </div>
        </div>
        <div style="background: #2D6A4F; padding: 15px; text-align: center;">
            <p style="color: #74C69D; margin: 0; font-size: 12px;">SmartAgri — Cluster Alert System 🌱</p>
        </div>
    </div>
    """
    for email in to_emails:
        await send_email(email, subject, html)

async def send_order_confirmation(to_email: str, product_name: str, quantity: int, price: float):
    subject = f"✅ Order Confirmed – {product_name} | SmartAgri"
    html = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #FAFAF7; border-radius: 16px; overflow: hidden;">
        <div style="background: linear-gradient(135deg, #2D6A4F, #74C69D); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 24px;">✅ Order Confirmed</h1>
        </div>
        <div style="padding: 30px;">
            <div style="background: #E8F5E9; border-radius: 12px; padding: 20px;">
                <p style="margin: 5px 0;"><strong>📦 Product:</strong> {product_name}</p>
                <p style="margin: 5px 0;"><strong>🔢 Quantity:</strong> {quantity}</p>
                <p style="margin: 5px 0;"><strong>💰 Total:</strong> ₹{price * quantity}</p>
                <p style="margin: 5px 0;"><strong>🚚 Delivery:</strong> Within 2 days</p>
            </div>
        </div>
        <div style="background: #2D6A4F; padding: 15px; text-align: center;">
            <p style="color: #74C69D; margin: 0; font-size: 12px;">SmartAgri — Home Delivery 🌱</p>
        </div>
    </div>
    """
    await send_email(to_email, subject, html)

async def send_vendor_introduction(vendor_email: str, vendor_name: str, farmer_name: str, farmer_email: str, crop_name: str):
    subject = f"🌿 New Farmer Interest – {crop_name} | SmartAgri"
    html = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #FAFAF7; border-radius: 16px; overflow: hidden;">
        <div style="background: linear-gradient(135deg, #D4A847, #F5D060); padding: 30px; text-align: center;">
            <h1 style="color: #333; margin: 0; font-size: 24px;">🌿 New Farmer Interest</h1>
        </div>
        <div style="padding: 30px;">
            <p>Dear {vendor_name},</p>
            <p>A SmartAgri farmer is interested in growing <strong>{crop_name}</strong> and would like to connect with you as a potential buyer.</p>
            <div style="background: #FFF8E1; border-radius: 12px; padding: 20px; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>🧑‍🌾 Farmer:</strong> {farmer_name}</p>
                <p style="margin: 5px 0;"><strong>📧 Email:</strong> {farmer_email}</p>
                <p style="margin: 5px 0;"><strong>🌱 Crop:</strong> {crop_name}</p>
            </div>
            <p>Please reach out to them to discuss pricing and purchase arrangements.</p>
        </div>
        <div style="background: #2D6A4F; padding: 15px; text-align: center;">
            <p style="color: #74C69D; margin: 0; font-size: 12px;">SmartAgri — Connecting Farmers & Markets 🌱</p>
        </div>
    </div>
    """
    await send_email(vendor_email, subject, html)
