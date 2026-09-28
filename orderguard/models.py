from dataclasses import dataclass
from datetime import datetime

@dataclass
class Address:
    # TODO fields:
       country: str   
       province: str  
       zip_code: str  

    

@dataclass
class Order:
    # TODO fields:
       order_id: str
       email: str
       total_cents: int     
       billing: Address
       shipping: Address
       is_first_order: bool
       created_at: datetime
    

@dataclass
class RuleResult:
    # TODO fields:
       points: int
       reason: str  