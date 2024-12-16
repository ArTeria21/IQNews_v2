from .callback_handlers import router as callback_router
from .command_handlers import router as command_router
from .text_handlers import router as text_router

__all__ = ["command_router", "text_router", "callback_router"]
