from mongoengine import Document, StringField, FloatField, IntField


class Product(Document):

    key = IntField(primary_key=True)
    stock = IntField(required=True)
    name = StringField(required=True)
    desc = StringField(required=False)
    price = FloatField(default=True)
    multimedia = StringField()