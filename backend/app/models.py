from pydantic import BaseModel

class Article(BaseModel):
    title: str
    url: str
    source: str
    summary: str
