from mongoengine import Document, StringField, ListField, ReferenceField, IntField, GenericEmbeddedDocumentField

class InformativeSection(Document):
    id = StringField()
    multimedia = GenericEmbeddedDocumentField() #soporta cualquier tipo de multimedia
    text = StringField()