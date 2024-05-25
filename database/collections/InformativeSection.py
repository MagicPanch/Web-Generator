from mongoengine import Document, StringField, DictField


class InformativeSection(Document):
    id = StringField(primary_key=True)
    type = StringField(required=True)
    title = StringField(required=True)
    texts = DictField(required=False)