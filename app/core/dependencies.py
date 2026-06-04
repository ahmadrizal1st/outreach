"""
Centralized FastAPI dependencies.

Import `templates` dari sini di semua route agar tidak perlu
mendefinisikan path template berulang-ulang di setiap file.
"""
import os
from fastapi.templating import Jinja2Templates

# Path tunggal ke folder templates, relatif terhadap file ini
_templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
templates = Jinja2Templates(directory=_templates_dir)
