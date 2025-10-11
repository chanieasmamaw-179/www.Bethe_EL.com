from flask import Flask, request, jsonify, Response, send_from_directory
import smtplib
from flask_cors import CORS
from email.message import EmailMessage
import os
from dotenv import load_dotenv
import logging
import datetime
import traceback

# --- Initialize App ---
app = Flask(__name__)

# --- Configure CORS ---
CORS(app, resources={
    r"/*": {
        "origins": ["https://www-bethe-el-com.onrender.com", "http://localhost:5001"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "supports_credentials": True
    }
})

# --- Logging setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Load environment variables ---
load_dotenv()

EMAIL_ADDRESS = 'chanieasmamaw@yahoo.com'
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
TO_EMAILS = ['chanieasmamaw@yahoo.com', 'elsa32@walla.com']

# --- Health check ---
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.datetime.now().isoformat()})


# --- Debug config ---
@app.route('/debug-config', methods=['GET'])
def debug_config():
    return jsonify({
        'EMAIL_CONFIGURED': bool(EMAIL_PASSWORD),
        'EMAIL_ADDRESS': EMAIL_ADDRESS,
        'TO_EMAILS': TO_EMAILS,
        'SERVER_TIME': datetime.datetime.now().isoformat()
    })


# --- Root route ---
@app.route('/', methods=['GET'])
def home():
    return "✅ Flask Email Registration Server is running. Use POST /register."


# --- Serve form.js dynamically ---
@app.route('/form.js', methods=['GET'])
def serve_javascript():
    js_content = """
document.addEventListener('DOMContentLoaded', function() {
    const API_BASE_URL = window.location.hostname === 'localhost'
        ? 'http://localhost:5001'
        : 'https://www-bethe-el-com-app.onrender.com';

    const forms = document.querySelectorAll('form[id*="registration"], form[id*="Registration"], form[id*="interest"], form[id*="Interest"]');

    forms.forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault();

            const btn = form.querySelector('button[type="submit"], input[type="submit"]');
            const msgBox = form.querySelector('.message') || document.getElementById('message');
            if (btn) { btn.disabled = true; btn.textContent = 'Submitting...'; }
            if (msgBox) msgBox.style.display = 'none';

            const formData = {
                name: form.querySelector('[name="name"], #name')?.value || '',
                email: form.querySelector('[name="email"], #email')?.value || '',
                program: form.querySelector('[name="program"], #program')?.value || '',
                registration_interest: form.querySelector('textarea, #message-text')?.value || '',
                role: form.querySelector('[name="role"], #role')?.value || 'participant'
            };

            try {
                const res = await fetch(`${API_BASE_URL}/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });
                const result = await res.json();

                if (res.ok && result.status === 'success') {
                    msgBox.className = 'message success';
                    msgBox.textContent = result.message;
                    msgBox.style.display = 'block';
                    form.reset();
                } else {
                    msgBox.className = 'message error';
                    msgBox.textContent = result.message || 'Registration failed.';
                    msgBox.style.display = 'block';
                }
            } catch (err) {
                msgBox.className = 'message error';
                msgBox.textContent = 'Network error. Please try again.';
                msgBox.style.display = 'block';
                console.error(err);
            } finally {
                if (btn) { btn.disabled = false; btn.textContent = 'Submit'; }
            }
        });
    });
});
"""
    return Response(js_content, mimetype='application/javascript')


# --- Email Test ---
@app.route('/test-email', methods=['GET'])
def test_email():
    if not EMAIL_PASSWORD:
        return jsonify({'status': 'fail', 'message': 'EMAIL_PASSWORD not configured'}), 500
    try:
        with smtplib.SMTP_SSL('smtp.mail.yahoo.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            msg = EmailMessage()
            msg['Subject'] = '✅ Test Email - Flask App'
            msg['From'] = EMAIL_ADDRESS
            msg['To'] = ', '.join(TO_EMAILS)
            msg.set_content('This is a test email to verify the SMTP setup.')
            smtp.send_message(msg)
        return jsonify({'status': 'success', 'message': 'Test email sent successfully!'})
    except Exception as e:
        logger.error(f"Email test failed: {str(e)}")
        return jsonify({'status': 'fail', 'message': f'Email test failed: {str(e)}'}), 500


# --- Registration Endpoint ---
@app.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 204

    if not EMAIL_PASSWORD:
        logger.error("EMAIL_PASSWORD not configured")
        return jsonify({'status': 'fail', 'message': 'Server email configuration missing'}), 500

    try:
        data = request.json or {}
        logger.info(f"Register endpoint hit with data: {data}")

        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        role = data.get('role', 'participant').strip()
        program = data.get('program', '').strip()
        registration_interest = (data.get('registration_interest') or data.get('message', '')).strip()

        if not name or not email:
            return jsonify({'status': 'fail', 'message': 'Please enter both name and email.'}), 400

        # --- Compose admin email ---
        is_program_registration = bool(program)
        admin_msg = EmailMessage()
        admin_msg['From'] = EMAIL_ADDRESS
        admin_msg['To'] = ', '.join(TO_EMAILS)
        admin_msg['Subject'] = f'New Program Registration: {program}' if is_program_registration else f'New Interest Registration - Role: {role}'
        content = f"""
Name: {name}
Email: {email}
Role: {role}
Program: {program or 'N/A'}
Message: {registration_interest or 'N/A'}
Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        admin_msg.set_content(content)

        # --- Send emails ---
        with smtplib.SMTP_SSL('smtp.mail.yahoo.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(admin_msg)
            logger.info("Admin email sent.")

            # Confirmation email to user
            confirm_msg = EmailMessage()
            confirm_msg['From'] = EMAIL_ADDRESS
            confirm_msg['To'] = email
            confirm_msg['Subject'] = 'Thank you for registering!'
            confirm_msg.set_content(f"Dear {name},\n\nThank you for registering with Beit-El Tibeb.\n\n{content}")
            smtp.send_message(confirm_msg)

        reg_id = f"REG-{datetime.datetime.now().strftime('%Y%m%d')}-{hash(email) % 10000:04d}"
        return jsonify({'status': 'success', 'message': 'Registration submitted successfully!', 'registration_id': reg_id}), 200

    except smtplib.SMTPAuthenticationError:
        return jsonify({'status': 'fail', 'message': 'Email authentication failed. Please check email credentials.'}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({'status': 'fail', 'message': 'Registration service temporarily unavailable. Please try again later.'}), 500


# --- Favicon ---
@app.route('/favicon.ico', methods=['GET'])
def favicon():
    try:
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                   'favicon.ico', mimetype='image/vnd.microsoft.icon')
    except FileNotFoundError:
        return '', 204


# --- Run app ---
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
