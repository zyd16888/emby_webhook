from pydantic import BaseModel

class ServerInfo(BaseModel):
    Name: str
    Id: str
    Version: str
