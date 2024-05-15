from mongoengine import Document, StringField, ListField, ReferenceField, IntField, GenericEmbeddedDocumentField

class ShopSection(Document):
    id = StringField(required=True)
    images = ListField(GenericEmbeddedDocumentField()) #soporta cualquier tipo de multimedia
    cart = ListField(required=True)
    filter = #definir el tipo
    product = ListField(required=True)
    browser = StringField(required=True)