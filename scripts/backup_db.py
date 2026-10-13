"""
Backup de la base de datos local SQLite antes de migrar/desplegar.
Uso: python scripts/backup_db.py [ruta_db]
Para Turso remoto use: turso db shell <db> .dump > backup.sql
"""
import os
import shutil
import sys
from datetime import datetime

origen = sys.argv[1] if len(sys.argv) > 1 else "superchampion.db"
if not os.path.exists(origen):
    print(f"❌ No existe {origen}")
    sys.exit(1)
destino = f"{origen}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy2(origen, destino)
print(f"✅ Backup creado: {destino}")
