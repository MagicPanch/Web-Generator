from database.collections.general.Page import Page
from mongoengine import Document, StringField, ListField, ReferenceField, IntField, BooleanField

class User(Document):

    id = IntField(primary_key=True)
    username = StringField(required=False)
    name = StringField(required=False)
    paginas = ListField(ReferenceField(Page), required=False)
    hizo_tutorial = BooleanField(default=False)