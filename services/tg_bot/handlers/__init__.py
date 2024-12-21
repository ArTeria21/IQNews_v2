from .admin_panel import router as admin_panel_router
from .callback_handlers import router as callback_router
from .command_handlers import router as command_router
from .information_handlers import router as information_router
from .text_handlers import router as text_router

__all__ = ["command_router", "text_router", "callback_router", "admin_panel_router", "information_router"]
