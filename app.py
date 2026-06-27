from flask import Flask, request, jsonify, Response
import smtplib
import socket
from flask_cors import CORS
from email.message import EmailMessage
import os
from dotenv import load_dotenv
import logging
import datetime

app = Flask(__name__)

# Configure CORS to allow requests from your website.
# Includes common local dev origins:
#  - http://localhost:3000        (typical node/react dev server)
#  - http://localhost:63342       (JetBrains IDE built-in preview server)
#  - http://127.0.0.1:63342       (same, via IP instead of hostname)
CORS(app, origins=[
    "https://www-bethe-el-com.onrender.com",
    "http://localhost:3000",
    "http://localhost:63342",
    "http://127.0.0.1:63342",
])

# Enable detailed logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Configure your email settings
EMAIL_ADDRESS = 'chanieasmamaw@yahoo.com'
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
TO_EMAILS = ['chanieasmamaw@yahoo.com', 'elsa32@walla.com']

# ============================================================
# SMTP helper with a hard timeout and STARTTLS (587) instead
# of SMTP_SSL (465). Render's free-tier outbound networking
# can hang or silently drop long-lived SSL connections on 465,
# which causes the whole request to hang until Render's proxy
# kills it with a 502 - instead of returning a clean JSON error.
# STARTTLS on 587 is more reliable across cloud providers, and
# the explicit timeout means a bad connection fails fast with
# a real error message instead of hanging.
# ============================================================
SMTP_HOST = 'smtp.mail.yahoo.com'
SMTP_PORT = 587          # STARTTLS port (was 465/SSL)
SMTP_TIMEOUT_SECONDS = 15


def send_via_smtp(messages):
    """
    Connects once and sends one or more EmailMessage objects.
    Raises on failure so callers can catch and report a clean error.
    `messages` is a list of EmailMessage instances.
    """
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT_SECONDS) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        for msg in messages:
            smtp.send_message(msg)


# Health check endpoint
@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.datetime.now().isoformat()})


@app.route('/')
def home():
    return "Flask Email Server is running! Use POST /register for registrations."


# Rest of your existing endpoints remain the same...
@app.route('/test-email', methods=['GET'])
def test_email():
    """Test endpoint to check email configuration"""
    if not EMAIL_PASSWORD:
        return jsonify({'status': 'fail', 'message': 'EMAIL_PASSWORD not configured'}), 500

    try:
        msg = EmailMessage()
        msg['Subject'] = 'Test Email - Flask App'
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = ', '.join(TO_EMAILS)
        msg.set_content('This is a test email to verify the email configuration is working.')

        logger.info(f"Connecting to {SMTP_HOST}:{SMTP_PORT} with {SMTP_TIMEOUT_SECONDS}s timeout...")
        send_via_smtp([msg])
        logger.info("Test email sent successfully!")
        return jsonify({'status': 'success', 'message': 'Test email sent successfully!'})

    except socket.timeout:
        logger.error(f"SMTP connection timed out after {SMTP_TIMEOUT_SECONDS}s")
        return jsonify({
            'status': 'fail',
            'message': f'SMTP connection timed out after {SMTP_TIMEOUT_SECONDS}s. '
                        f'The hosting network may be blocking outbound SMTP.'
        }), 504

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication failed: {str(e)}")
        return jsonify({
            'status': 'fail',
            'message': 'Email authentication failed. The Yahoo app password may be wrong, '
                        'expired, or revoked. Generate a new one in Yahoo Account Security.'
        }), 500

    except (smtplib.SMTPException, OSError) as e:
        logger.error(f"Email test failed: {str(e)}")
        return jsonify({'status': 'fail', 'message': f'Email test failed: {str(e)}'}), 500


@app.route('/register', methods=['POST'])
def register():
    """Unified registration endpoint that handles both program applications and general interest registrations"""
    logger.info("Registration request received")

    if not EMAIL_PASSWORD:
        logger.error("EMAIL_PASSWORD not configured")
        return jsonify({'status': 'fail', 'message': 'Email configuration error'}), 500

    data = request.json
    logger.info(f"Received data: {data}")

    if not data:
        logger.error("No data provided in request")
        return jsonify({'status': 'fail', 'message': 'No data provided'}), 400

    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    role = data.get('role', 'participant').strip()
    program = data.get('program', '').strip()

    registration_interest = data.get('registration_interest', '') or data.get('message', '')
    registration_interest = registration_interest.strip()

    logger.info(f"Parsed data - Name: {name}, Email: {email}, Role: {role}, Program: {program}")

    if not name or not email:
        logger.error("Missing required fields")
        return jsonify({'status': 'fail', 'message': 'Missing required fields: name and email'}), 400

    try:
        is_program_registration = bool(program)
        program_display = None

        admin_msg = EmailMessage()

        if is_program_registration:
            admin_msg['Subject'] = 'New Program Registration - Ethiopian Cultural Heritage'

            program_names = {
                'basket-weaving': 'Traditional Basket Weaving',
                'coffee-ceremony': 'Ethiopian Coffee Ceremony',
                'textile-arts': 'Traditional Textile Arts',
                'pottery': 'Pottery & Clay Arts',
                'culinary': 'Culinary Heritage',
                'immersion': 'Cultural Immersion Program'
            }
            program_display = program_names.get(program, program)

            admin_content = "=== NEW PROGRAM REGISTRATION ===\n\n"
            admin_content += f"Full Name: {name}\n"
            admin_content += f"Email Address: {email}\n"
            admin_content += f"Role: {role.title()}\n"
            admin_content += f"Interested Program: {program_display}\n"

            if registration_interest:
                admin_content += f"\nAdditional Information:\n{registration_interest}\n"

            admin_content += "\n" + "=" * 40 + "\n"
            admin_content += f"Registration submitted at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        else:
            if role.lower() == 'organization':
                admin_msg['Subject'] = 'New Interest Registration - Art Exhibition Website (Organization)'
                admin_content = f'This is the registration report from organization\n\nName: {name}\nEmail: {email}\nRole: {role}'
            elif role.lower() == 'artist':
                admin_msg['Subject'] = 'New Interest Registration - Art Exhibition Website (Artist)'
                admin_content = f'Role: artist\nName: {name}\nEmail: {email}\nRole: {role}'
            else:
                admin_msg['Subject'] = 'New Interest Registration - Art Exhibition Website'
                admin_content = f'Name: {name}\nEmail: {email}\nRole: {role}'

            if registration_interest:
                admin_content += f'\nAdditional Info: {registration_interest}'

            admin_content += f"\n\nSubmitted at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        admin_msg['From'] = EMAIL_ADDRESS
        admin_msg['To'] = ', '.join(TO_EMAILS)
        admin_msg.set_content(admin_content)

        messages_to_send = [admin_msg]

        reg_id = None
        if is_program_registration:
            user_msg = EmailMessage()
            user_msg['Subject'] = 'Registration Confirmation - Ethiopian Cultural Heritage Programs'
            user_msg['From'] = EMAIL_ADDRESS
            user_msg['To'] = email

            reg_id = f"ECH-{datetime.datetime.now().strftime('%Y%m%d')}-{hash(email) % 10000:04d}"

            user_content = f"Dear {name},\n\n"
            user_content += "Thank you for your interest in our Ethiopian Cultural Heritage Programs!\n\n"
            user_content += "We have received your registration with the following details:\n\n"
            user_content += f"• Name: {name}\n"
            user_content += f"• Email: {email}\n"
            user_content += f"• Role: {role.title()}\n"
            user_content += f"• Program of Interest: {program_display}\n"

            if registration_interest:
                user_content += f"• Your Message: {registration_interest}\n"

            user_content += f"• Registration ID: {reg_id}\n\n"
            user_content += "Our team will review your application and contact you within 2-3 business days to discuss the next steps.\n\n"
            user_content += "If you have any immediate questions, please don't hesitate to contact us at chanieasmamaw@yahoo.com.\n\n"
            user_content += "Best regards,\n"
            user_content += "Ethiopian Cultural Heritage Programs Team"

            user_msg.set_content(user_content)
            messages_to_send.append(user_msg)

        logger.info(f"Connecting to {SMTP_HOST}:{SMTP_PORT} with {SMTP_TIMEOUT_SECONDS}s timeout...")
        send_via_smtp(messages_to_send)
        logger.info(f"Sent {len(messages_to_send)} email(s) successfully!")

        if is_program_registration:
            return jsonify({
                'status': 'success',
                'message': 'Registration submitted successfully! Please check your email for confirmation details.',
                'registration_id': reg_id
            }), 200

        return jsonify({
            'status': 'success',
            'message': 'Registration sent successfully!'
        }), 200

    except socket.timeout:
        logger.error(f"SMTP connection timed out after {SMTP_TIMEOUT_SECONDS}s")
        return jsonify({
            'status': 'fail',
            'message': 'Could not send email right now (connection to the mail server timed out). '
                        'Please try again in a moment.'
        }), 504

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication failed: {str(e)}")
        return jsonify(
            {'status': 'fail', 'message': 'Email authentication failed. Please check email credentials.'}), 500

    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {str(e)}")
        return jsonify({'status': 'fail', 'message': f'Email delivery failed: {str(e)}'}), 500

    except OSError as e:
        # Covers connection refused / network unreachable / DNS failures
        logger.error(f"Network error talking to SMTP server: {str(e)}")
        return jsonify({
            'status': 'fail',
            'message': 'Could not reach the mail server right now. Please try again shortly.'
        }), 502

    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        return jsonify({'status': 'fail', 'message': 'Registration failed. Please try again later.'}), 500


@app.route('/send-email', methods=['POST'])
def send_email_redirect():
    """Legacy endpoint - redirects to unified register endpoint for backward compatibility"""
    logger.info("Legacy /send-email endpoint called - redirecting to /register")
    return register()


@app.route('/favicon.ico')
def favicon():
    return '', 404


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)