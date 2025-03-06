from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities.invoice import Invoice

class InvoiceRepository(ABC):
    @abstractmethod
    def save(self, invoice: Invoice) -> str:
        pass

    @abstractmethod
    def update(self, invoice: Invoice) -> None:
        pass

    @abstractmethod
    def find_by_id(self, invoice_id: str) -> Optional[Invoice]:
        pass

    @abstractmethod
    def find_all(self) -> List[Invoice]:
        pass

    @abstractmethod
    def find_pending(self) -> List[Invoice]:
        pass
