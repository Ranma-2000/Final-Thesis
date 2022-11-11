from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Item(BaseModel):
    text: str


@app.post("/")
def root(data: Item):
    return {"message": f"You wrote:"}