from typing import List, Optional
from pymongo import MongoClient
from ....domain.entities.invoice import Invoice
from ....domain.repositories.invoice_repository import InvoiceRepository

class MongoInvoiceRepository(InvoiceRepository):
    def __init__(self, mongo_uri: str, db_name: str, collection_name: str):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def save(self, invoice: Invoice) -> str:
        data = self._to_dict(invoice)
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    def update(self, invoice: Invoice) -> None:
        data = self._to_dict(invoice)
        self.collection.update_one(
            {'_id': invoice.id},
            {'$set': data}
        )

    # ... rest of the implementation

    def _to_dict(self, invoice: Invoice) -> dict:
        return {
            # Implement conversion from Invoice to dict
            pass
        }

    def _from_dict(self, data: dict) -> Invoice:
        return Invoice(
            # Implement conversion from dict to Invoice
            pass
        )
