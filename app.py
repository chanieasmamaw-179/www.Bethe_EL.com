from flask import Flask, request, jsonify, Response
import smtplib
from flask_cors import CORS
from flask import send_from_directory
from email.message import EmailMessage
import os
from dotenv import load_dotenv
import logging
import datetime

app = Flask(__name__)
CORS(app)

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

# Configure your email settings
EMAIL_ADDRESS = 'chanieasmamaw@yahoo.com'
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
TO_EMAILS = ['chanieasmamaw@yahoo.com', 'yehunchanieasmamaw@gmail.com']

# Debug: Check if environment variables are loaded
print(f"EMAIL_PASSWORD loaded: {'Yes' if EMAIL_PASSWORD else 'No'}")
print(f"EMAIL_ADDRESS: {EMAIL_ADDRESS}")
print(f"TO_EMAILS: {TO_EMAILS}")


@app.route('/')
def home():
    return "Flask Email Server is running! Use POST /register for registrations."


@app.route('/form.js')
def serve_javascript():
    """Serve the JavaScript file for form handling"""
    javascript_content = """
document.addEventListener('DOMContentLoaded', function() {
    // Handle both registration forms and interest forms
    const forms = document.querySelectorAll('form[id*="registration"], form[id*="Registration"], form[id*="interest"], form[id*="Interest"]');

    forms.forEach(form => {
        form.addEventListener('submit', async function(e) {
            e.preventDefault(); // Prevent default form submission

            const submitBtn = form.querySelector('input[type="submit"], button[type="submit"]') || 
                            form.querySelector('#submitBtn') || 
                            form.querySelector('button');
            const messageDiv = form.querySelector('#message') || 
                             document.getElementById('message') || 
                             form.querySelector('.message');

            // Disable submit button and show loading state
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Submitting...';
            }

            // Hide previous messages
            if (messageDiv) {
                messageDiv.style.display = 'none';
            }

            // Collect form data - flexible field detection
            const formData = {
                name: form.querySelector('#name')?.value || 
                      form.querySelector('[name="name"]')?.value || 
                      form.querySelector('input[type="text"]')?.value || '',

                email: form.querySelector('#email')?.value || 
                       form.querySelector('[name="email"]')?.value || 
                       form.querySelector('input[type="email"]')?.value || '',

                program: form.querySelector('#program')?.value || 
                         form.querySelector('[name="program"]')?.value || 
                         form.querySelector('select')?.value || '',

                registration_interest: form.querySelector('#message-text')?.value || 
                                     form.querySelector('#message')?.value || 
                                     form.querySelector('[name="message"]')?.value || 
                                     form.querySelector('textarea')?.value || '',

                role: form.querySelector('#role')?.value || 
                      form.querySelector('[name="role"]')?.value || 
                      form.querySelector('select[name*="role"]')?.value || 
                      'participant' // Default role
            };

            console.log('Submitting form data:', formData);

            try {
                // Always use the unified /register endpoint
                const response = await fetch('/register', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(formData)
                });

                const result = await response.json();

                if (response.ok && result.status === 'success') {
                    // Success
                    if (messageDiv) {
                        messageDiv.className = 'message success';
                        messageDiv.textContent = result.message;
                        messageDiv.style.display = 'block';
                    }

                    // Reset form
                    form.reset();

                    // Show registration ID if provided
                    if (result.registration_id) {
                        setTimeout(() => {
                            if (messageDiv) {
                                messageDiv.innerHTML = result.message + '<br><strong>Registration ID: ' + result.registration_id + '</strong>';
                            }
                        }, 500);
                    }
                } else {
                    // Error from server
                    if (messageDiv) {
                        messageDiv.className = 'message error';
                        messageDiv.textContent = result.message || 'Registration failed. Please try again.';
                        messageDiv.style.display = 'block';
                    }
                }

            } catch (error) {
                // Network or other error
                console.error('Registration Error:', error);
                if (messageDiv) {
                    messageDiv.className = 'message error';
                    messageDiv.textContent = 'Network error. Please check your connection and try again.';
                    messageDiv.style.display = 'block';
                }
            } finally {
                // Re-enable submit button
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Submit';
                }
            }
        });
    });
});



// Additional utility functions
function showMessage(message, type = 'info') {
    const messageDiv = document.getElementById('message') || document.querySelector('.message');
    if (messageDiv) {
        messageDiv.className = 'message ' + type;
        messageDiv.textContent = message;
        messageDiv.style.display = 'block';

        // Auto-hide success messages after 5 seconds
        if (type === 'success') {
            setTimeout(() => {
                messageDiv.style.display = 'none';
            }, 5000);
        }
    }
}

function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validateForm(form) {
    const name = form.querySelector('#name, [name="name"]')?.value?.trim();
    const email = form.querySelector('#email, [name="email"]')?.value?.trim();

    if (!name) {
        showMessage('Please enter your name', 'error');
        return false;
    }

    if (!email) {
        showMessage('Please enter your email address', 'error');
        return false;
    }

    if (!validateEmail(email)) {
        showMessage('Please enter a valid email address', 'error');
        return false;
    }

    return true;
}

// Enhanced form validation
document.addEventListener('DOMContentLoaded', function() {
    const emailInputs = document.querySelectorAll('#email, [name="email"], input[type="email"]');
    emailInputs.forEach(emailInput => {
        emailInput.addEventListener('blur', function() {
            const email = this.value.trim();
            if (email && !validateEmail(email)) {
                showMessage('Please enter a valid email address', 'error');
            }
        });
    });
});
"""

    response = Response(javascript_content, mimetype='application/javascript')
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/test-email', methods=['GET'])
def test_email():
    """Test endpoint to check email configuration"""
    if not EMAIL_PASSWORD:
        return jsonify({'status': 'fail', 'message': 'EMAIL_PASSWORD not configured'}), 500

    try:
        # Test SMTP connection
        with smtplib.SMTP_SSL('smtp.mail.yahoo.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            logger.info("SMTP connection successful!")

            # Send test email
            msg = EmailMessage()
            msg['Subject'] = 'Test Email - Flask App'
            msg['From'] = EMAIL_ADDRESS
            msg['To'] = ', '.join(TO_EMAILS)
            msg.set_content('This is a test email to verify the email configuration is working.')

            smtp.send_message(msg)
            return jsonify({'status': 'success', 'message': 'Test email sent successfully!'})

    except Exception as e:
        logger.error(f"Email test failed: {str(e)}")
        return jsonify({'status': 'fail', 'message': f'Email test failed: {str(e)}'}), 500


@app.route('/register', methods=['POST'])
def register():
    """Unified registration endpoint that handles both program applications and general interest registrations"""
    logger.info("Registration request received")

    # Check if email password is configured
    if not EMAIL_PASSWORD:
        logger.error("EMAIL_PASSWORD not configured")
        return jsonify({'status': 'fail', 'message': 'Email configuration error'}), 500

    data = request.json
    logger.info(f"Received data: {data}")

    if not data:
        logger.error("No data provided in request")
        return jsonify({'status': 'fail', 'message': 'No data provided'}), 400

    # Extract form data - handle multiple field names for backward compatibility
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    role = data.get('role', 'participant').strip()
    program = data.get('program', '').strip()

    # Handle both field names for backward compatibility
    registration_interest = data.get('registration_interest', '') or data.get('message', '')
    registration_interest = registration_interest.strip()

    logger.info(f"Parsed data - Name: {name}, Email: {email}, Role: {role}, Program: {program}")

    # Validate required fields
    if not name or not email:
        logger.error("Missing required fields")
        return jsonify({'status': 'fail', 'message': 'Missing required fields: name and email'}), 400

    try:
        # Determine registration type based on presence of program field
        is_program_registration = bool(program)

        # Create admin notification email
        admin_msg = EmailMessage()

        if is_program_registration:
            # Program registration email
            admin_msg['Subject'] = 'New Program Registration - Ethiopian Cultural Heritage'

            # Program names mapping
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
            # General interest registration email
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

        # Send admin notification
        logger.info("Attempting to connect to SMTP server...")
        with smtplib.SMTP_SSL('smtp.mail.yahoo.com', 465) as smtp:
            logger.info("SMTP connection established")
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            logger.info("SMTP login successful")

            smtp.send_message(admin_msg)
            logger.info("Admin notification email sent successfully!")

            # Send user confirmation only for program registrations
            if is_program_registration:
                user_msg = EmailMessage()
                user_msg['Subject'] = 'Registration Confirmation - Ethiopian Cultural Heritage Programs'
                user_msg['From'] = EMAIL_ADDRESS
                user_msg['To'] = email

                # Generate a simple registration ID
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
                smtp.send_message(user_msg)
                logger.info("User confirmation email sent successfully!")

                return jsonify({
                    'status': 'success',
                    'message': 'Registration submitted successfully! Please check your email for confirmation details.',
                    'registration_id': reg_id
                }), 200

        # For general interest registrations
        return jsonify({
            'status': 'success',
            'message': 'Registration sent successfully!'
        }), 200

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication failed: {str(e)}")
        return jsonify(
            {'status': 'fail', 'message': 'Email authentication failed. Please check email credentials.'}), 500
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {str(e)}")
        return jsonify({'status': 'fail', 'message': f'Email delivery failed: {str(e)}'}), 500
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
    return send_from_directory('static', 'favicon.ico')


if __name__ == '__main__':
    print("Starting Flask app with debug logging...")
    print(f"Email configuration check:")
    print(f"- EMAIL_ADDRESS: {EMAIL_ADDRESS}")
    print(f"- EMAIL_PASSWORD configured: {'Yes' if EMAIL_PASSWORD else 'No'}")
    print(f"- TO_EMAILS: {TO_EMAILS}")
    app.run(debug=True)