from mongoengine import *
import collections

DB_NAME = "susamuru"
PORT = 27017

connect(db=DB_NAME, host='localhost', port=PORT)
print("Mongo Client is created!")

class Entity(Document):
    disambiguation_term = StringField(required=True)
    candidate = StringField(required=True)
    sentence = StringField(required=True)


def add_entity(entity):
    try:
        entity.save()
    except ValidationError:
        print("Please check the structure of the entity")
