from mongoengine import Document, StringField, DateTimeField, ListField, GenericReferenceField, BooleanField, IntField


class Page(Document):

    id = StringField(primary_key=True)
    name = StringField(required=True)
    contact = StringField(required=False)
    creationDate = DateTimeField(required=True)
    compilationDate = DateTimeField(required=False)
    lastModificationDate = DateTimeField(required=True)
    mail = StringField(required=False)
    location = StringField(required=False)
    sections = ListField(GenericReferenceField())
    has_ecomm_section = BooleanField(default=False)
    product_counter = IntField(required=False, default=0)