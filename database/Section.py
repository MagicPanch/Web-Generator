from mongoengine import Document, StringField, ListField, ReferenceField, IntField

class Section(Document):
    id = StringField(required=True)