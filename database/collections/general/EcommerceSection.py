from mongoengine import Document, StringField


class EcommerceSection(Document):
    id = StringField(primary_key=True)
    type = StringField(required=True)