from pymongo import MongoClient
import collections

DB_NAME = "susamuru"
PORT = 27017
client = MongoClient()

client = MongoClient('localhost', PORT)
print("Mongo Client is created!")

db = client[DB_NAME]
print("Database is created!")

disambiguation_terms = db.disambiguation_terms

def add_disambiguation_terms(elements):
    if not isinstance(elements,collections.Sequence):
        print("Elements has to be a list of disambiguation terms")
        return
    
    result = disambiguation_terms.insert_many(elements)
    print('Multiple disambiguation terms are inserted: {0}'.format(result.inserted_ids))