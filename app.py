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
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')  # This will read from .env file
TO_EMAIL = 'chanieasmamaw@yahoo.com'  # Where to receive the form data


@app.route('/')
def home():
    return "Flask Email Server is running! Use POST /send-email to send emails."

@app.route('/send-email', methods=['POST'])
def send_email():
    data = request.json

    name = data.get('name')
    email = data.get('email')
    role = data.get('role')

    if not name or not email or not role:
        return jsonify({'status': 'fail', 'message': 'Missing fields'}), 400

    # Compose the email
    msg = EmailMessage()
    msg['Subject'] = 'New Registration from Art Exhibition Website'
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = TO_EMAIL
    msg.set_content(f'Name: {name}\nEmail: {email}\nRole: {role}')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return jsonify({'status': 'success', 'message': 'Email sent!'}), 200
    except Exception as e:
        return jsonify({'status': 'fail', 'message': str(e)}), 500

@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico')  # If you have a favicon.ico file in a 'static' folder

if __name__ == '__main__':
    app.run(debug=True)
