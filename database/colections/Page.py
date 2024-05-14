from mongoengine import Document, StringField, DateField, BooleanField


class Page(Document):

    id = StringField(primary_key=True)
    name = StringField(required=True)
    contact = StringField(required=False)
    creationDate = DateField(required=True)
    lastModification = DateField(required=True)
    compiled = BooleanField()
    mail = StringField(required=False)
    location = StringField(required=False)