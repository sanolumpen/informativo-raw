# InformativoRaw — Pasquin Opción 6

Genera y publica un pasquin de noticias en formato Opción 6 (solo texto, 
compatible con WhatsApp y Telegram).

## Flujo de trabajo

```bash
# 1. Generar borrador desde la base de noticias-raw
python3 borrador.py --limit 15

# 2. EDITAR borrador.txt con tu editor (curar, reordenar, ajustar)

# 3. Publicar a Telegram + archivar + GitHub Pages
python3 publish.py
```

## Canales

- **Telegram:** https://t.me/+yzn1KN3WYsFjNTRh
- **Web (GitHub Pages):** https://sanolumpen.github.io/informativo-raw/

## Dependencias

- Python 3.10+
- requests
- Base de datos local de noticias-raw (`~/Documentos/Proyectos/noticias-raw/`)
