from abc import ABC, abstractmethod
from typing import Dict
from ....domain.entities.invoice import Invoice

class ProcessInvoiceUseCase(ABC):
    @abstractmethod
    def process_image(self, image_data: bytes) -> Invoice:
        pass

    @abstractmethod
    def verify_invoice(self, invoice_id: str, data: Dict) -> Invoice:
        pass
