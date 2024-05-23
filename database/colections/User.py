from mongoengine import Document, StringField, ListField, ReferenceField, IntField, BooleanField

from database.colections import Page


class User(Document):

    id = IntField(primary_key=True)
    username = StringField(required=False)
    name = StringField(required=False)
    paginas = ListField(ReferenceField(Page))
    hizo_tutorial = BooleanField(default=False)