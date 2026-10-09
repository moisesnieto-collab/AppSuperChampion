# AppSuperChampion 🏆

Aplicación moderna e independiente optimizada para la gestión de campeonatos de fútbol escolar y formativo por **Categorías** (1° a 6° Básico), **Días** (Día 1 y Día 2) y **Grupos**.

## Características Principales
- **Navegación Ágil**: Selección instantánea por Categoría ➔ Día ➔ Grupo.
- **2 Roles de Acceso**:
  - **Modo Consulta (Público / Padres / Delegados)**: Acceso directo sin clave; visualización de tablas en tiempo real y resultados.
  - **Modo Organizador (Mesa de Control)**: Desbloqueo rápido por PIN (4 dígitos); creación y reinicio de categorías, registro rápido de marcadores (`2 - 1 💾`) y generación de partidos de desempate / final.
- **Tabla de Posiciones en Tiempo Real**: Cálculo automático de PJ, PG, PE, PP, GF, GC, DG y Pts con criterios oficiales de desempate.
- **Definición de Campeón del Día**: Puntero automático o generación de partido de desempate ante empate en el primer lugar.
- **Persistencia Híbrida**: Soporte nativo para SQLite local y Turso Cloud (LibSQL).

## Ejecución
```bash
source venv/bin/activate
python main.py
```

## Pruebas
```bash
python -m unittest discover -v -s tests -t .
```
