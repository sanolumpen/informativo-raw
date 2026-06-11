# InformativoRaw

Genera y publica un pasquin de noticias en formato Telegram.

## Flujo de trabajo

```bash
# 1. Generar + formatear pasquin desde la base de noticias-raw
python3 ../noticias-raw/pasquin_data.py --limit 15 --json --section-names specific \
  | python3 formatear_pasquin.py > borrador.txt

# 2. EDITAR borrador.txt con tu editor (curar, reordenar, ajustar)

# 3. Publicar a Telegram + archivar + GitHub Pages
python3 publish.py
```

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
