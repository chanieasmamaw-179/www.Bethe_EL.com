from flask import Flask, request, jsonify
import smtplib
from email.message import EmailMessage

app = Flask(__name__)

# Configure your email settings
EMAIL_ADDRESS = 'your_email@gmail.com'
EMAIL_PASSWORD = 'your_app_password'  # Use Gmail App Password if 2FA is on
TO_EMAIL = 'destination_email@gmail.com'  # Where to receive the form data

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

if __name__ == '__main__':
    app.run(debug=True)
