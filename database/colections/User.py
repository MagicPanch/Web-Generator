from mongoengine import Document, StringField, ListField, ReferenceField, IntField


class User(Document):
    id = IntField(primary_key=True)
    username = StringField(required=False)
    name = StringField(required=False)
    paginas = ListField(ReferenceField('Page'))