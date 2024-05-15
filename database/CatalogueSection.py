from mongoengine import Document, StringField, ListField, ReferenceField, IntField, GenericEmbeddedDocumentField

class CatalogueSection(Document):
    id = StringField(required=True)
    product = ListField(required=True)