from dotenv import load_dotenv
from os import environ

load_dotenv()


class AppConfig:
    secret_key = environ.get("SECRET_KEY")
    passwords_salt = environ.get("PASSWORDS_SALT")
    db_name = environ.get("DB_NAME")
    db_host = environ.get("DB_HOST")
    db_port = int(environ.get("DB_PORT"))
    db_user = environ.get("DB_USER")
    db_password = environ.get("DB_PASSWORD")
    public_base_url = environ.get("PUBLIC_BASE_URL", "http://localhost:5000")
