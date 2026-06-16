# InformativoRaw

Genera y publica un pasquin de noticias en formato Telegram.

## Flujo de trabajo

### Publicación completa (Telegram + archivo + GitHub Pages)

```bash
# 1. Generar + formatear pasquin desde la base de noticias-raw
python3 ../noticias-raw/pasquin_data.py --limit 15 --json --section-names specific \
  | python3 formatear_pasquin.py > borrador.txt

# 2. EDITAR borrador.txt con tu editor (curar, reordenar, ajustar)

# 3. Publicar a Telegram + archivar + GitHub Pages
python3 publish.py
```

### Con `/pasquin` (interactivo, vía OpenCode)

El comando `/pasquin` ejecuta el flujo completo con selección del usuario:

```
/pasquin N=20
  ↓
1. Muestra lista de noticias disponibles con IDs por sección
2. Elegís qué IDs incluir ("todos", "102,105,201", "solo nacionales")
3. Genera el pasquin con solo esos IDs
4. Te muestra el resultado
5. Espera tu aprobación ("publicálo") para enviar a Telegram
```

Definido en `opencode.json`. Usa `pasquin_data.py` como única fuente de datos
(evita consultas divergentes que antes deformaban el resultado).

### Solo Telegram

```bash
# Publicar solo a Telegram (sin archivar ni git push)
python3 publish.py --solo-telegram
```

El flag `--solo-telegram` salta: archivo histórico, GitHub Pages, git push y limpieza del borrador.  
El borrador se conserva para poder re-publicar si es necesario.

## Formateador (`formatear_pasquin.py`)

Toma el JSON de `pasquin_data.py --json` y produce texto Telegram listo para publicar:

- Header + fecha
- Cadena de titulares (4 headlines)
- Secciones con emojis: 🌎 🇦🇷 📍 ✅ 🌤️
- Artículos numerados con 🔹
- Detección IA (🤖), propaganda (⚠️), chequeado (✅❌)
- Siempre incluye FUENTES y link al canal
- Auto-truncado a 4096 chars (retrocede previews hasta que entre)

## Canales

- **Telegram:** https://t.me/+yzn1KN3WYsFjNTRh
- **Web (GitHub Pages):** https://sanolumpen.github.io/informativo-raw/

## Dependencias

- Python 3.10+
- requests
- Base de datos local de noticias-raw (`~/Documentos/Proyectos/noticias-raw/`)
