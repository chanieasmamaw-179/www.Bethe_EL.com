from flask import Flask, request, jsonify
import smtplib
from flask_cors import CORS
from flask import send_from_directory
from email.message import EmailMessage
import os
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

load_dotenv()

# Configure your email settings
EMAIL_ADDRESS = 'chanieasmamaw@yahoo.com'
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
TO_EMAILS = ['chanieasmamaw@yahoo.com', 'yehunchanieasmamaw@gmail.com']

# Debug: Check if environment variables are loaded (remove in production)
print(f"EMAIL_PASSWORD loaded: {'Yes' if EMAIL_PASSWORD else 'No'}")


@app.route('/')
def home():
    return "Flask Email Server is running! Use POST /send-email to send emails."


@app.route('/send-email', methods=['POST'])
def send_email():
    # Check if email password is configured
    if not EMAIL_PASSWORD:
        return jsonify({'status': 'fail', 'message': 'Email configuration error'}), 500

    data = request.json
    if not data:
        return jsonify({'status': 'fail', 'message': 'No data provided'}), 400

    name = data.get('name')
    registration_interest = data.get('registration_interest')  # Fixed the key name
    email = data.get('email')
    role = data.get('role')

    if not name or not email or not role:
        return jsonify({'status': 'fail', 'message': 'Missing required fields: name, email, role'}), 400

    # Compose the email
    msg = EmailMessage()
    msg['Subject'] = 'New Registration from Art Exhibition Website'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = ', '.join(TO_EMAILS)  # Join multiple emails with comma

    # Format email content based on role
    if role.lower() == 'organization':
        email_content = f'This is the registration report from organization\n\nName: {name}\nEmail: {email}\nRole: {role}'
    elif role.lower() == 'artist':
        email_content = f'Role: artist\nName: {name}\nEmail: {email}\nRole: {role}'
    else:
        # Default format for other roles
        email_content = f'Name: {name}\nEmail: {email}\nRole: {role}'

    # Add registration interest if provided
    if registration_interest:
        email_content += f'\nAdditional Info: {registration_interest}'

    msg.set_content(email_content)

    try:
        # Use Yahoo SMTP server
        with smtplib.SMTP_SSL('smtp.mail.yahoo.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return jsonify({'status': 'success', 'message': 'Email sent successfully!'}), 200
    except smtplib.SMTPAuthenticationError:
        return jsonify({'status': 'fail', 'message': 'Email authentication failed. Check credentials.'}), 500
    except smtplib.SMTPException as e:
        return jsonify({'status': 'fail', 'message': f'SMTP error: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'status': 'fail', 'message': f'Unexpected error: {str(e)}'}), 500


@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico')


if __name__ == '__main__':
    app.run(debug=True)