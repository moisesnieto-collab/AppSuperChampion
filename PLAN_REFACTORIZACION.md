# Plan de Refactorización - AppSuperChampion

## Objetivo
Refactorizar la aplicación para soportar múltiples campeonatos y copas con una jerarquía más completa y escalable.

## Jerarquía Final

```
Año → Campeonato → Copa → Torneo → Jornada → Categoría → Grupo
```

### Requerimientos Adicionales
- **Jornada**: Debe tener campos `lugar` y `horario`
- **Permisos**: Organizador y Master a nivel Campeonato
- **CRUD**: Crear y eliminar en TODAS las secciones

---

## Fase 1: Diseño de Modelos y Schema (2-3 días)

### 1. Diseñar nuevos modelos

#### Modelo Anio
- `id`: INTEGER PRIMARY KEY
- `valor`: INTEGER (ej: 2024)
- `orden`: INTEGER DEFAULT 0
- `activo`: BOOLEAN DEFAULT 1

#### Modelo Campeonato
- `id`: INTEGER PRIMARY KEY
- `nombre`: TEXT NOT NULL
- `anio_id`: INTEGER FOREIGN KEY → anios.id
- `orden`: INTEGER DEFAULT 0
- `activo`: BOOLEAN DEFAULT 1

#### Modelo Copa
- `id`: INTEGER PRIMARY KEY
- `nombre`: TEXT NOT NULL
- `campeonato_id`: INTEGER FOREIGN KEY → campeonatos.id
- `orden`: INTEGER DEFAULT 0
- `activo`: BOOLEAN DEFAULT 1

#### Actualización Modelo Jornada
- Agregar `lugar`: TEXT
- Agregar `horario`: TEXT (formato HH:MM)

### 2. Diseñar sistema de permisos

#### Tabla campeonato_permisos
- `id`: INTEGER PRIMARY KEY
- `campeonato_id`: INTEGER FOREIGN KEY → campeonatos.id
- `usuario_id`: INTEGER FOREIGN KEY → usuarios.id
- `rol`: TEXT (organizador/master)
- `fecha_asignacion`: DATETIME

### 3. Diseñar schema de base de datos

#### Nuevas tablas
- `anios`
- `campeonatos`
- `copas`
- `campeonato_permisos`

#### Tablas a actualizar
- `torneos`: agregar `copa_id` (FOREIGN KEY → copas.id)
- `jornadas`: agregar `lugar` (TEXT), `horario` (TEXT)

#### Constraints
- Foreign keys con CASCADE DELETE
- Índices para búsquedas frecuentes
- Unique constraints donde sea necesario

### 4. Planificar migración de datos

#### Script de migración
1. Crear año actual (ej: 2024)
2. Crear campeonato por defecto (ej: "Supercampeones")
3. Crear copa por defecto (ej: "Copa Supercampeones")
4. Migrar torneos existentes a la copa por defecto
5. Migrar permisos existentes a nivel campeonato
6. Validar integridad de datos

---

## Fase 2: Backend - Base de Datos (2-3 días)

### 5. Implementar schema
- Crear archivo de migración SQL
- Ejecutar migración en desarrollo
- Validar estructura de tablas
- Crear índices y constraints

### 6. Ejecutar migración de datos
- Backup de base de datos actual
- Ejecutar script de migración
- Validar datos migrados
- Verificar integridad referencial

---

## Fase 3: Backend - Modelos (2 días)

### 7. Crear modelos
- `backend/models/anio.py`
- `backend/models/campeonato.py`
- `backend/models/copa.py`

### 8. Actualizar modelos existentes
- `backend/models/torneo.py`: agregar `copa_id`
- `backend/models/jornada.py`: agregar `lugar`, `horario`
- `backend/models/usuario.py`: actualizar si es necesario

---

## Fase 4: Backend - Repositorios (2-3 días)

### 9. Crear repositorios
- `AnioRepository` en `backend/database/repositories.py`
  - `obtener_todos()`
  - `obtener_por_id()`
  - `obtener_activo()`
  - `crear()`
  - `actualizar()`
  - `eliminar()`
  - `actualizar_orden()`

- `CampeonatoRepository` en `backend/database/repositories.py`
  - `obtener_todos()`
  - `obtener_por_id()`
  - `obtener_por_anio()`
  - `obtener_activo()`
  - `crear()`
  - `actualizar()`
  - `eliminar()`
  - `actualizar_orden()`

- `CopaRepository` en `backend/database/repositories.py`
  - `obtener_todos()`
  - `obtener_por_id()`
  - `obtener_por_campeonato()`
  - `obtener_activo()`
  - `crear()`
  - `actualizar()`
  - `eliminar()`
  - `actualizar_orden()`

- `CampeonatoPermisoRepository` en `backend/database/repositories.py`
  - `obtener_por_campeonato()`
  - `obtener_por_usuario()`
  - `asignar_permiso()`
  - `revocar_permiso()`
  - `verificar_permiso()`

### 10. Actualizar repositorios existentes
- `TorneoRepository`: filtrar por `copa_id`
- `JornadaRepository`: incluir `lugar` y `horario` en selects
- `UsuarioRepository`: manejo de permisos por campeonato

---

## Fase 5: Backend - Servicios (3-4 días)

### 11. Crear servicios
- `backend/services/anio_service.py`
  - `obtener_anios()`
  - `crear_anio()`
  - `actualizar_anio()`
  - `eliminar_anio()`
  - `actualizar_orden_anio()`

- `backend/services/campeonato_service.py`
  - `obtener_campeonatos()`
  - `obtener_campeonatos_por_anio()`
  - `crear_campeonato()`
  - `actualizar_campeonato()`
  - `eliminar_campeonato()`
  - `actualizar_orden_campeonato()`
  - `asignar_permiso()`
  - `revocar_permiso()`
  - `verificar_permiso_usuario()`

- `backend/services/copa_service.py`
  - `obtener_copas()`
  - `obtener_copas_por_campeonato()`
  - `crear_copa()`
  - `actualizar_copa()`
  - `eliminar_copa()`
  - `actualizar_orden_copa()`

### 12. Actualizar servicios existentes
- `TorneoService`: filtrar por copa, verificar permisos de campeonato
- `JornadaService`: manejar `lugar` y `horario`
- `UsuarioService`: verificar permisos por campeonato
- `PartidoService`: verificar permisos por campeonato
- `CategoriaService`: verificar permisos por campeonato
- `GrupoService`: verificar permisos por campeonato

---

## Fase 6: Frontend - UI Jerarquía (3-4 días)

### 13. Diseñar selector multi-nivel
- Actualizar `frontend/components/selector_categoria.py`
- Agregar selector de Año (chips con crear/eliminar)
- Agregar selector de Campeonato (chips con crear/eliminar)
- Agregar selector de Copa (chips con crear/eliminar)
- Mantener selector actual de Torneo/Jornada/Categoría/Grupo

### 14. Implementar modales de creación
- Modal crear/editar Año
- Modal crear/editar Campeonato (con selección de año)
- Modal crear/editar Copa (con selección de campeonato)
- Actualizar modal Jornada con campos Lugar y Horario

### 15. Implementar modales de eliminación
- Confirmación para Año (con validación de dependencias)
- Confirmación para Campeonato (con validación de dependencias)
- Confirmación para Copa (con validación de dependencias)

### 16. Actualizar estado global
- Estado para `anio_activo`, `campeonato_activo`, `copa_activa`
- Actualizar flujo de navegación en `main.py`
- Actualizar `actualizar_vista()` para manejar nuevos niveles

---

## Fase 7: Frontend - UI CRUD (2-3 días)

### 17. Agregar CRUD en secciones existentes
- Categoría: botones crear/eliminar (si no existen)
- Grupo: botones crear/eliminar (si no existen)
- Validar que TODAS las secciones tengan CRUD:
  - Año ✓
  - Campeonato ✓
  - Copa ✓
  - Torneo ✓ (ya existe)
  - Jornada ✓ (ya existe)
  - Categoría ✓ (verificar)
  - Grupo ✓ (verificar)

### 18. UI responsive para nuevos selectores
- Adaptar diseño para 7 niveles de jerarquía
- Asegurar responsividad en móviles
- Optimizar espacio en pantalla
- Usar wrap y scroll horizontal donde sea necesario

---

## Fase 8: Sistema de Permisos (2 días)

### 19. Implementar UI de permisos
- Modal para asignar organizador/master a campeonato
- Lista de usuarios por campeonato con roles
- Botón para agregar usuario
- Botón para eliminar usuario/rol

### 20. Integrar permisos en UI
- Mostrar botones CRUD solo si tiene permisos
- Bloquear acciones sin permisos
- Mensajes de error claros cuando no hay permisos
- Verificar permisos en cada operación de CRUD

---

## Fase 9: Testing (2-3 días)

### 21. Tests de backend
- Tests para nuevos repositorios (Anio, Campeonato, Copa, Permiso)
- Tests para nuevos servicios
- Tests de migración de datos
- Tests de permisos
- Tests de integración entre niveles

### 22. Tests de frontend
- Tests de navegación por jerarquía
- Tests de CRUD en todas las secciones
- Tests de permisos en UI
- Tests de responsividad

### 23. Tests end-to-end
- Flujo completo: crear año → campeonato → copa → torneo → jornada → partido
- Validar permisos por campeonato
- Validar migración de datos existentes

---

## Fase 10: Despliegue (1 día)

### 24. Preparación
- Backup de producción
- Documentación de migración
- Checklist de validación

### 25. Despliegue
- Ejecutar migración en producción
- Validar funcionalidad
- Monitoreo post-despliegue
- Rollback plan si es necesario

---

## Estimación de Tiempo

**Total: 18-22 días** (aproximadamente 3-4 semanas)

### Desglose por fase
- Fase 1: 2-3 días
- Fase 2: 2-3 días
- Fase 3: 2 días
- Fase 4: 2-3 días
- Fase 5: 3-4 días
- Fase 6: 3-4 días
- Fase 7: 2-3 días
- Fase 8: 2 días
- Fase 9: 2-3 días
- Fase 10: 1 día

---

## Riesgos Principales

### Alto Riesgo
- **Migración de datos existentes**: Requiere cuidado extremo para no perder datos
- **Complejidad de UI**: 7 niveles de jerarquía pueden ser difíciles de manejar en móviles

### Riesgo Medio
- **Sistema de permisos**: Puede requerir ajustes durante implementación
- **Despliegue en producción**: Siempre existe riesgo de problemas

### Mitigación
- Backup antes de cada cambio mayor
- Testing exhaustivo en desarrollo
- Despliegue gradual con validación continua
- Rollback plan preparado

---

## Checklist de Validación

### Backend
- [ ] Schema de base de datos creado y validado
- [ ] Migración de datos ejecutada exitosamente
- [ ] Todos los modelos creados/actualizados
- [ ] Todos los repositorios creados/actualizados
- [ ] Todos los servicios creados/actualizados
- [ ] Permisos implementados correctamente
- [ ] Tests de backend pasando

### Frontend
- [ ] Selectores de Año, Campeonato, Copa implementados
- [ ] Modales de creación/edición implementados
- [ ] Modales de eliminación implementados
- [ ] CRUD en todas las secciones
- [ ] UI responsive validada
- [ ] Permisos integrados en UI
- [ ] Tests de frontend pasando

### Despliegue
- [ ] Backup de producción realizado
- [ ] Migración ejecutada en producción
- [ ] Validación post-despliegue completada
- [ ] Monitoreo activo

---

## Notas Adicionales

### Decisiones de Diseño
- **Año como tabla separada**: Permite múltiples años en el sistema
- **Permisos a nivel Campeonato**: Simplifica la gestión de permisos
- **Lugar y Horario en Jornada**: Información contextual importante para partidos

### Mejoras Futuras (No incluidas en este plan)
- Equipos/Clubes centralizados
- Jugadores por equipo
- Estadísticas globales (goleadores, MVPs)
- Fases (Fase de grupos, Octavos, etc.)
- Sedes como nivel separado
- Documentos adjuntos (reglamentos, actas)
- Notificaciones

### Comunicación
- Revisar progreso al final de cada fase
- Validar decisiones de diseño con stakeholders
- Ajustar plan según sea necesario
