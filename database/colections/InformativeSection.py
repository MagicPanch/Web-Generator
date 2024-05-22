from mongoengine import Document, StringField, DictField


class InformativeSection(Document):
    id = StringField(primary_key=True)
    title = StringField(required=True)
    text = StringField(required=False)
    texts = DictField(required=False)