from mongoengine import Document, StringField, EmailField


class UserModel(Document):
    first_name = StringField(required=True, max_length=30, min_length=3)
    last_name = StringField(required=True, max_length=30, min_length=2)
    email = EmailField(unique=True, required=True, max_length=64, min_length=5)
    password = StringField(required=True, max_length=255)
