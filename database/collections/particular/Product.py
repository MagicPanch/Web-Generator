from mongoengine import Document, StringField, FloatField, ListField, IntField, ObjectIdField


class Product(Document):

    id = StringField(primary_key=True)
    stock = IntField(required=True)
    name = StringField(required=True)
    desc = StringField(required=False)
    prize = FloatField(default=True)
    multimedia = ListField(StringField())