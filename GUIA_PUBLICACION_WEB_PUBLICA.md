# Guía paso a paso: página pública (Cloudflare Pages + R2)

Arquitectura: Turso (BD) → `exportar_datos_publicos.py` (en tu Mac o un worker) → `datos.json` en Cloudflare R2 → `web_publica/index.html` en Cloudflare Pages lee ese JSON. La app Flet queda solo para organizadores.

## 0. Seguridad previa
1. Verifica que `.env` esté en `.gitignore`.
2. Tu `TURSO_TOKEN` se compartió en claro: revócalo en Turso (`turso db tokens invalidate superchampion` y `turso db tokens create superchampion`) y actualiza `.env` y Render.

## 1. Crear el bucket R2
1. Cloudflare Dashboard → R2 Object Storage → Create bucket (ej. `superchampion-datos`).
2. Bucket → Settings → Public access → habilita "R2.dev subdomain". Copia la URL `https://pub-xxxx.r2.dev`.
3. Bucket → Settings → CORS Policy, pega:
```json
[{"AllowedOrigins":["https://TU-PROYECTO.pages.dev"],"AllowedMethods":["GET"],"AllowedHeaders":["*"],"MaxAgeSeconds":3600}]
```
(Para pruebas locales agrega también `http://localhost:8000`.)

## 2. Crear credenciales de escritura
1. R2 → Manage API Tokens → Create API token, permiso "Object Read & Write", limitado a tu bucket.
2. Guarda: Account ID, Access Key ID, Secret Access Key.

## 3. Configurar el exportador
1. Instala dependencias: `venv/bin/pip install -r requirements.txt` (incluye `boto3`).
2. Añade a `.env` (nunca a git):
```
R2_ACCOUNT_ID=...
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
R2_BUCKET=superchampion-datos
```
3. Prueba una vez: `venv/bin/python scripts/exportar_datos_publicos.py`. Debe imprimir "datos.json actualizado" y "datos.json subido a R2".
4. Comprueba en el navegador `https://pub-xxxx.r2.dev/datos.json`.

## 4. Apuntar la página a R2
En `web_publica/index.html` cambia:
```js
const DATOS_URL = "https://pub-xxxx.r2.dev/datos.json";
```

## 5. Publicar la página en Cloudflare Pages
1. Sube los cambios a GitHub (`git add`, `commit`, `push` a `main`).
2. Cloudflare → Workers & Pages → Create → Pages → Connect to Git → tu repo.
3. Framework: None. Build command: vacío. Build output directory: `web_publica`.
4. Deploy. Obtendrás `https://TU-PROYECTO.pages.dev`. Actualiza el CORS del paso 1 con esa URL exacta.

## 6. Mantener datos.json actualizado
Opción Mac (torneo puntual): en una terminal, desde la raíz del proyecto
```
venv/bin/python scripts/exportar_datos_publicos.py --cada 15
```
El Mac debe estar encendido, sin suspensión y con internet. Para evitar suspensión: `caffeinate -d` en otra terminal.

Opción Render (producción): crea un Background Worker con el mismo repo.
- Build: `pip install -r requirements.txt`
- Start: `python scripts/exportar_datos_publicos.py --cada 15`
- Variables de entorno: `TURSO_URL`, `TURSO_TOKEN`, `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET`.

## 7. Verificación
1. Abre la URL de Pages en el celular: verás Marcadores, Tabla y Estado.
2. En la app Flet (organizador) cambia un marcador; en ~15–25 s debe verse en la página.
3. Si aparece "Sin conexión": revisa CORS y `DATOS_URL`.

## 8. Antes del torneo
- Haz una prueba de carga ligera abriendo la página en varios dispositivos.
- Plan Turso recomendado: Developer. La página pública casi no consulta Turso (solo el exportador, cada 15 s).
- Sube `index.html` con `git push`: Pages se redespliega solo.

## Notas
- La app Flet y la página pública son independientes: si el exportador se detiene, la página muestra el último dato ("Actualizado hace X s").
- Los datos de R2 son públicos: no incluyen PIN ni datos sensibles.
