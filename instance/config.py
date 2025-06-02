i# Default config for SSO
SSO_HOST = 'https://sso.dev.offsec.nat.bt.com'
SSO_LOGIN_URL = '/auth/user/login'
SSO_MACHINE_LOGIN_URL = '/auth/machine/login'
SSO_VALIDATE_URL='/auth/user/validate'
VERIFY_CERTS=False

# SQLAlchemy default
SQLALCHEMY_DATABASE_URI = ''


# Flask defaults
from uuid import uuid4
SECRET_KEY = uuid4().hex
SESSION_TYPE = 'filesystem'
SESSION_COOKIE_SECURE = True

# Specific config for this app
