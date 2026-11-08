from mongoengine import DateTimeField, Document, StringField


class RevokedToken(Document):
    jti = StringField(required=True, unique=True)
    expires_at = DateTimeField(required=True)
    meta = {"indexes": [{"fields": ["expires_at"], "expireAfterSeconds": 0}]}
