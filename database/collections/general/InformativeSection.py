from mongoengine import Document, StringField


class InformativeSection(Document):
    id = StringField(primary_key=True)
    type = StringField(required=True)
    title = StringField(required=True)
    text = StringField(required=False)