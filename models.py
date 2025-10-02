# -----------------------------
# Models
# -----------------------------

from pydantic import BaseModel

class AskRequest(BaseModel):
    document_id: str
    question: str