from mongoengine import Document, StringField, DateField, BooleanField


class Page(Document):

    id = StringField(primary_key=True)
    name = StringField(required=True)
    contact = StringField(required=False)
    creationDate = DateField(required=True)
    compilationDate = DateField(required=False)
    lastModification = DateField(required=True)
    mail = StringField(required=False)
    location = StringField(required=False)