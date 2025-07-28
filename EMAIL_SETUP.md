# Email Configuration Setup

## For Gmail (Recommended)

1. **Get Gmail App Password:**
   - Go to your Gmail account settings
   - Enable 2-factor authentication
   - Generate an "App Password" for this application
   - Use this app password (not your regular password)

2. **Update settings.py:**
   Replace these lines in `school_management/settings.py`:
   ```python
   EMAIL_HOST_USER = 'your-email@gmail.com'  # Replace with your Gmail
   EMAIL_HOST_PASSWORD = 'your-app-password'  # Replace with your Gmail app password
   DEFAULT_FROM_EMAIL = 'School Management System <your-email@gmail.com>'
   ```

3. **For Development Testing:**
   To see emails in terminal instead of sending real emails, uncomment this line:
   ```python
   EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
   ```

## How to Use Password Reset

1. **Admin Login:**
   - Username: `admin`
   - Password: `admin123`

2. **Password Reset API Endpoints:**
   - **Forgot Password:** `POST /api/auth/forgot-password/`
     - Body: `{"email": "user@example.com"}`
   
   - **Reset Password:** `POST /api/auth/reset-password/`
     - Body: `{"token": "reset-token-from-email", "new_password": "newpassword"}`

3. **Reset Flow:**
   - User enters email in forgot password form
   - System sends email with reset link
   - User clicks link and enters new password
   - Password is updated, user can login with new password

## Testing

You can test the password reset functionality by:
1. Creating a test user with a valid email
2. Requesting password reset
3. Checking your email for the reset link
4. Using the token from the email to reset password