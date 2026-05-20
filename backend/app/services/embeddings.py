from fastembed import TextEmbedding
from app.config import settings

_model = None


def _get_model():
    global _model
    if _model is None:
        _model = TextEmbedding(model_name=settings.embedding_model)
    return _model


def generate_embedding(text: str) -> list[float]:
    model = _get_model()
    result = list(model.embed(text))
    return result[0].tolist()
