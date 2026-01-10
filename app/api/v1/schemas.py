from pydantic import BaseModel

class ProductCreate(BaseModel):
    code: str
    description: str

class ProductOut(BaseModel):
    id: int
    code: str
    description: str
    active: bool

    class Config:
        from_attributes = True
