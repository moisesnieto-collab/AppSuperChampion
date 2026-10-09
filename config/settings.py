import os
from dotenv import load_dotenv

load_dotenv()

# Título y temas
APP_TITLE = "SuperChampion 🏆 Gestión de Torneos"
APP_THEME_MODE = "dark"
APP_BGCOLOR = "#0A0E17"

# Base de datos Turso / SQLite
TURSO_URL = os.getenv("TURSO_URL", "superchampion.db")
TURSO_TOKEN = os.getenv("TURSO_TOKEN", "")

# Seguridad PIN Organizador
ORGANIZADOR_PIN = os.getenv("ORGANIZADOR_PIN", "1234")
