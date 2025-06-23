# Default config for SSO
SSO_HOST = 'https://sso.dev.offsec.nat.bt.com'
SSO_LOGIN_URL = '/auth/user/login'
SSO_MACHINE_LOGIN_URL = '/auth/machine/login'
SSO_VALIDATE_URL='/auth/user/validate'
VERIFY_CERTS=False

# SQLAlchemy default
SQLALCHEMY_DATABASE_URI = ''

# Flask defaults
SECRET_KEY = 'your-secret-key-here'  # Replace this with a secure random key in production
SESSION_TYPE = 'filesystem'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# Specific config for this app
