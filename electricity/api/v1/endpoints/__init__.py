# electricity/api/v1/endpoints/__init__.py
from .tarifliste import router as tarifliste_router
from .spotprices import router as spotprices_router

__all__ = ['tarifliste_router', 'spotprices_router']
