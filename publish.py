#!/usr/bin/env python3
"""Publica el pasquin: Telegram + archivo + GitHub Pages."""

import json
import os
import shutil
import sys
import subprocess
from datetime import datetime

REPO_DIR = os.path.dirname(os.path.abspath(__file__))
BORRADOR_PATH = os.path.join(REPO_DIR, "borrador.txt")
DOCS_DIR = os.path.join(REPO_DIR, "docs")
ARCHIVO_DIR = os.path.join(DOCS_DIR, "archivo")
TOKEN_PATH = os.path.join(REPO_DIR, "token.txt")
CHAT_ID_PATH = os.path.join(REPO_DIR, "chat_id.txt")

MONTHS_ES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]
WEEKDAYS_ES = [
    "lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo",
]


def format_date_es(dt: datetime) -> str:
    wd = WEEKDAYS_ES[dt.weekday()]
    return f"{wd}, {dt.day} de {MONTHS_ES[dt.month]} de {dt.year}"


def load_token() -> str:
    token = os.environ.get("TELEGRAM_TOKEN")
    if token:
        return token
    if not os.path.exists(TOKEN_PATH):
        print("ERROR: No se encuentra token.txt ni TELEGRAM_TOKEN env")
        print("Creá el archivo con tu token de Telegram Bot:")
        print(f"  echo 'TU_TOKEN' > {TOKEN_PATH}")
        print("  export TELEGRAM_TOKEN='TU_TOKEN'")
        sys.exit(1)
    token = open(TOKEN_PATH).read().strip()
    if not token:
        print("ERROR: token.txt está vacío")
        sys.exit(1)
    return token


def load_chat_id() -> str:
    cid = os.environ.get("TELEGRAM_CHAT_ID")
    if cid:
        return cid
    if os.path.exists(CHAT_ID_PATH):
        return open(CHAT_ID_PATH).read().strip()
    return None


def save_chat_id(chat_id: str):
    with open(CHAT_ID_PATH, "w") as f:
        f.write(chat_id.strip())
    print(f"chat_id guardado: {chat_id}")


def split_message(text, max_len=4000):
    """Divide un texto en chunks que no superen max_len caracteres."""
    lines = text.split("\n")
    chunks = []
    current = ""
    for line in lines:
        if len(line) > max_len:
            if current:
                chunks.append(current)
                current = ""
            for i in range(0, len(line), max_len):
                chunks.append(line[i:i+max_len])
            continue
        if current and len(current) + len(line) + 1 > max_len:
            chunks.append(current)
            current = line
        elif current:
            current += "\n" + line
        else:
            current = line
    if current:
        chunks.append(current)
    return chunks


def send_telegram(token, chat_id, text):
    import requests
    chunks = split_message(text)
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    for i, chunk in enumerate(chunks):
        payload = {
            "chat_id": chat_id,
            "text": chunk,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }
        resp = requests.post(url, json=payload, timeout=30)
        data = resp.json()
        if not data.get("ok"):
            print(f"ERROR Telegram (chunk {i+1}/{len(chunks)}): {data.get('description', 'error desconocido')}")
            return False

    if len(chunks) > 1:
        print(f"✓ Publicado en Telegram ({len(chunks)} mensajes, chat_id: {chat_id})")
    else:
        print(f"✓ Publicado en Telegram (chat_id: {chat_id})")
    return True


def resolve_chat_id(token):
    """Intenta resolver el chat_id del canal usando getUpdates."""
    import requests
    print("Resolviendo chat_id del canal...")
    print("  Enviá un mensaje cualquiera al canal ahora (ej: 'hola').")
    print("  Esperando...")
    import time
    for _ in range(30):
        url = f"https://api.telegram.org/bot{token}/getUpdates"
        resp = requests.get(url, timeout=30)
        data = resp.json()
        if data.get("ok") and data.get("result"):
            for update in data["result"]:
                msg = update.get("channel_post") or update.get("message")
                if msg:
                    chat = msg.get("chat", {})
                    cid = str(chat.get("id", ""))
                    title = chat.get("title", "canal")
                    if cid:
                        print(f"  ✓ Canal detectado: {title} (id: {cid})")
                        return cid
        time.sleep(2)
    print("  No se detectó ningún mensaje en 60 segundos.")
    return None


def archive_pasquin(text, date_str):
    os.makedirs(ARCHIVO_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    archivo_path = os.path.join(ARCHIVO_DIR, f"{today}.txt")
    with open(archivo_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"✓ Archivado: {archivo_path}")
    return archivo_path


def update_docs(text, date_str):
    os.makedirs(DOCS_DIR, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>InformativoRaw — {date_str}</title>
<style>
  body {{
    font-family: 'Courier New', Courier, monospace;
    max-width: 720px;
    margin: 2em auto;
    padding: 0 1em;
    background: #fafafa;
    color: #111;
    line-height: 1.5;
    white-space: pre-wrap;
    word-wrap: break-word;
  }}
  .footer {{
    margin-top: 2em;
    padding-top: 1em;
    border-top: 1px solid #ccc;
    font-size: 0.9em;
    color: #666;
    text-align: center;
  }}
  .nav {{
    text-align: center;
    margin-bottom: 1em;
    font-size: 0.9em;
  }}
  .nav a {{
    color: #3366cc;
    text-decoration: none;
  }}
  .nav a:hover {{
    text-decoration: underline;
  }}
</style>
</head>
<body>
<div class="nav">
  <a href="https://t.me/+yzn1KN3WYsFjNTRh">Canal de Telegram</a>
  &middot;
  <a href="archivo/">Archivo histórico</a>
</div>
{text}
<div class="footer">
  InformativoRaw — <a href="https://github.com/sanolumpen/informativo-raw">GitHub</a>
</div>
</body>
</html>"""

    index_path = os.path.join(DOCS_DIR, "index.html")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✓ Página actualizada: {index_path}")

    return index_path


def update_archive_index():
    """Genera un index.html para el archivo histórico."""
    if not os.path.exists(ARCHIVO_DIR):
        return
    files = sorted(
        [f for f in os.listdir(ARCHIVO_DIR) if f.endswith(".txt")],
        reverse=True,
    )
    if not files:
        return

    links = []
    for fname in files:
        date_part = fname.replace(".txt", "")
        links.append(
            f'    <li><a href="{fname}">{date_part}</a></li>'
        )

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Archivo — InformativoRaw</title>
<style>
  body {{
    font-family: 'Courier New', Courier, monospace;
    max-width: 720px;
    margin: 2em auto;
    padding: 0 1em;
    background: #fafafa;
    color: #111;
  }}
  ul {{
    list-style: none;
    padding: 0;
  }}
  li {{
    margin: 0.5em 0;
  }}
  a {{
    color: #3366cc;
    text-decoration: none;
  }}
  a:hover {{
    text-decoration: underline;
  }}
  .back {{
    margin-bottom: 1em;
  }}
</style>
</head>
<body>
<div class="back"><a href="../">← Volver</a></div>
<h1>Archivo InformativoRaw</h1>
<ul>
{chr(10).join(links)}
</ul>
</body>
</html>"""

    os.makedirs(ARCHIVO_DIR, exist_ok=True)
    archivo_index = os.path.join(ARCHIVO_DIR, "index.html")
    with open(archivo_index, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✓ Índice de archivo actualizado")


def git_push():
    """Commit y push al repo."""
    try:
        subprocess.run(
            ["git", "add", "-A"],
            cwd=REPO_DIR,
            capture_output=True, text=True, check=True,
        )
        result = subprocess.run(
            ["git", "diff", "--cached", "--quiet"],
            cwd=REPO_DIR,
            capture_output=True,
        )
        if result.returncode == 0:
            print("  Sin cambios nuevos para commit.")
            return

        today = datetime.now().strftime("%Y-%m-%d")
        subprocess.run(
            ["git", "commit", "-m", f"pasquin {today}"],
            cwd=REPO_DIR,
            capture_output=True, text=True, check=True,
        )
        subprocess.run(
            ["git", "push"],
            cwd=REPO_DIR,
            capture_output=True, text=True, check=True,
        )
        print(f"✓ Push a GitHub OK")
    except subprocess.CalledProcessError as e:
        print(f"  ⚠ Git: {e.stderr.strip()}")
        print("  Podés pushear manualmente después.")


def validar_pasquin(text: str) -> bool:
    """Valida que el borrador tenga formato de pasquin antes de publicar.
    Acepta dos formatos:
      - Telegram clásico: arranca con 📰 INFORMATIVORAW
      - ANCLA/cadena: arranca con ╔═══ ... PASQUIN
    """
    lines = text.strip().split("\n")
    if len(lines) < 3:
        print("ERROR: borrador.txt muy corto (menos de 3 líneas)")
        return False
    primera = lines[0]

    # Formato ANCLA / cadena informativa
    # Buscar "PASQUIN" en las primeras 3 líneas (el borde ╔ está en línea 1, el título en línea 2)
    if primera.startswith("╔") and any("PASQUIN" in l for l in lines[:3]):
        print("  ✓ Detectado formato ANCLA / cadena informativa")
        return True

    # Formato Telegram clásico
    if primera.startswith("\U0001f4f0 INFORMATIVORAW"):
        tiene_secciones = any(
            any(emoji in line for emoji in [
                "\U0001f1e6\U0001f1f7",  # 🇦🇷 NACIONALES
                "\U0001f310",            # 🌐 INTERNACIONALES
                "\U0001f4cd",            # 📍 PROVINCIAL / ZONA OESTE / LOCALES
                "\u26bd",                # ⚽ DEPORTES
                "\u2705",                # ✅ VERIFICACION
                "\U0001f324\ufe0f",      # 🌤️ CLIMA
                "\U0001f4f0",            # 📰 GENERAL
            ])
            for line in lines
        )
        if not tiene_secciones:
            print("ERROR: borrador.txt no contiene secciones con emojis")
            return False
        return True

    print(f"ERROR: borrador.txt no parece un pasquin (formato no reconocido)")
    print(f"  Primer línea: {primera[:80]}")
    print(f"  Formatos aceptados: 📰 INFORMATIVORAW | ╔═══ ... PASQUIN")
    return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Publica el pasquin en Telegram + archivo + GitHub Pages")
    parser.add_argument("--preview", action="store_true", help="Solo muestra el borrador sin publicar")
    parser.add_argument("--solo-telegram", action="store_true",
                        help="Solo publica en Telegram, sin archivar ni GitHub Pages ni git push")
    args = parser.parse_args()

    # --- 1) Leer borrador ---
    if not os.path.exists(BORRADOR_PATH):
        print("ERROR: No se encuentra borrador.txt")
        print("Primero generalo con: /pasquin --save")
        sys.exit(1)

    with open(BORRADOR_PATH, "r", encoding="utf-8") as f:
        pasquin_text = f.read().strip()

    if not pasquin_text:
        print("ERROR: borrador.txt está vacío")
        sys.exit(1)

    if not validar_pasquin(pasquin_text):
        respuesta = input("  ¿Publicar de todas formas? [s/N]: ")
        if respuesta.lower() != "s":
            sys.exit(1)

    if args.preview:
        print(pasquin_text)
        print(f"\n--- {len(pasquin_text)} caracteres ---")
        return

    today = datetime.now()
    date_str = format_date_es(today)
    date_iso = today.strftime("%Y-%m-%d")

    # --- 2) Telegram ---
    token = load_token()
    chat_id = load_chat_id()

    if not chat_id:
        print("chat_id no configurado. Resolviendo...")
        chat_id = resolve_chat_id(token)
        if chat_id:
            save_chat_id(chat_id)
        else:
            print("ERROR: No se pudo resolver el chat_id.")
            print("  Alternativa: enviale el link del canal a @username_to_id_bot")
            print("  y poné el ID numérico en chat_id.txt")
            sys.exit(1)

    telegram_ok = send_telegram(token, chat_id, pasquin_text)
    if not telegram_ok:
        print("  ⚠ No se pudo publicar en Telegram.")
        respuesta = input("  ¿Querés continuar igual (archivar + git)? [s/N]: ")
        if respuesta.lower() != "s":
            sys.exit(1)

    # --- 3) Archivar ---
    if not args.solo_telegram:
        archive_pasquin(pasquin_text, date_str)

    # --- 4) GitHub Pages ---
    if not args.solo_telegram:
        update_docs(pasquin_text, date_str)
        update_archive_index()

    # --- 5) Git push ---
    if not args.solo_telegram:
        git_push()

    # --- 6) Limpiar borrador ---
    if not args.solo_telegram:
        with open(BORRADOR_PATH, "w", encoding="utf-8") as f:
            f.write("")
        print("✓ borrador.txt limpiado (listo para la próxima)")
        print(f"\n✔ Publicación completa — {date_iso}")
    else:
        print(f"\n✔ Publicado solo en Telegram. El borrador queda en borrador.txt para re-publish.")


if __name__ == "__main__":
    main()
