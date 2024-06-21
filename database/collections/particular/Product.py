from mongoengine import Document, StringField, FloatField, IntField


class Product(Document):

    id = IntField(primary_key=True)
    stock = IntField(required=True)
    name = StringField(required=True)
    desc = StringField(required=False)
    price = FloatField(default=True)
    multimedia = StringField()