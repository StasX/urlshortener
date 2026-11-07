from mongoengine import Document, StringField, ReferenceField, IntField
from .user_model import UserModel


class UrlModel(Document):
    code = StringField(required=True, unique=True)
    short_url = StringField(required=True)
    full_url = StringField(required=True)
    enters = IntField(default=0)
    user = ReferenceField(UserModel, required=True)
