from mongoengine import Document, StringField, DateTimeField, ListField, ImageField

class Product(Document):
    id = StringField(primary_key=True)
    name = StringField(required=True)
    description = StringField(required=False)
    image = ImageField(required=True)
    price = IntField(required=True)

#instalar pillow para funcionamiento de image con: pip install Pillow