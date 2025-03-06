from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

@dataclass
class Company:
    name: str
    ruc: str
    address: Optional[str] = None
    phone: Optional[str] = None

@dataclass
class Stamping:
    number: str
    valid_from: str
    valid_until: str

@dataclass
class Product:
    name: str
    quantity: int
    unit_price: float
    total: float

@dataclass
class Invoice:
    id: Optional[str]
    company: Company
    stamping: Stamping
    invoice_number: str
    date: str
    customer_name: str
    customer_ruc: str
    products: List[Product]
    subtotal: float
    total: float
    status: str = 'pending'
    
    def calculate_totals(self) -> None:
        self.subtotal = sum(product.total for product in self.products)
        self.total = self.subtotal
