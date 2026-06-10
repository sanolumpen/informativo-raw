#!/usr/bin/env python3
"""Genera un pasquin estilo Opción 6 desde noticias-raw."""

import argparse
import json
import os
import re
import sys
from datetime import datetime

PROJECT_DIR = "/home/sanodesu/Documentos/Proyectos/noticias-raw"
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

from config import DB_PATH, SOURCES
from storage.sqlite_store import SqliteStore

ZONA_OESTE_SOURCES = {
    "UNMEDIO", "VIVIELOESTE", "ANTICIPOS", "ZOESTE", "OESTENOTI",
    "PRIMPLANO", "DIOESTE", "LACIUDAD", "ITUZAINGODIGITAL", "ANDIGITAL",
    "ZONANORTE",
}

ZONA_OESTE_LOCATIONS = {
    "Morón", "Ituzaingó", "Merlo", "Hurlingham", "Castelar", "Haedo",
    "Villa Tesei", "Libertad", "El Palomar", "Ramos Mejía", "San Justo",
    "La Tablada", "Lomas del Mirador", "Villa Luzuriaga", "Rafael Castillo",
    "González Catán", "Isidro Casanova", "Ciudad Evita", "Tapiales",
    "Aldo Bonzi",
}

NON_ARGENTINE_SOURCES = {"AP", "EFE", "REUTERS", "AFP", "DPA", "EUROPAPRESS"}

WEEKDAYS_ES = [
    "lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo",
]

MONTHS_ES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


def parse_classification(article: dict) -> dict:
    raw = article.get("classification", "{}")
    if not raw or raw.strip() == "{}":
        return {}
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}


def geo_infer_section(article: dict) -> str | None:
    source = article.get("source", "").upper()
    if source in NON_ARGENTINE_SOURCES:
        return "INTERNACIONALES"
    if source in ZONA_OESTE_SOURCES:
        return "ZONA OESTE"
    if source in SOURCES:
        return "NACIONALES"
    return None


def classify_article(article: dict) -> str:
    cls = parse_classification(article)
    topic = cls.get("topic", {})
    categoria = (topic.get("categoria") or "").lower()
    geo = cls.get("geo", {})
    nivel = (geo.get("nivel") or "").lower()
    partido = (geo.get("partido") or geo.get("localidad") or "").strip()
    source = article.get("source", "").upper()

    # 1) Deportes siempre primero por tema
    if "deporte" in categoria:
        return "DEPORTES"

    # 2) Zona Oeste por fuente o ubicación
    if source in ZONA_OESTE_SOURCES or partido in ZONA_OESTE_LOCATIONS:
        return "ZONA OESTE"

    # 3) Fuentes no argentinas → internacionales
    if source in NON_ARGENTINE_SOURCES:
        return "INTERNACIONALES"

    # 4) Fuentes argentinas → nacionales
    if source in SOURCES:
        return "NACIONALES"

    # 5) Fallback
    return "GENERAL"


def make_headline(title: str, max_len: int = 80) -> str:
    parts = title.split(":", 1)
    if len(parts) > 1 and len(parts[0].strip()) <= max_len:
        return parts[0].strip().upper()
    return title.strip().upper()


def truncate_at_word(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_space = truncated.rfind(" ")
    if last_space > max_chars * 0.7:
        truncated = truncated[:last_space]
    return truncated.strip()


def format_article(idx: int, article: dict) -> str:
    title = article.get("title", "").strip()
    preview = (article.get("preview") or "").strip()
    source = article.get("source", "")

    headline = make_headline(title)

    if preview and len(preview) >= 50:
        body = truncate_at_word(preview, 250)
        if not body.endswith((".", "!", "?")):
            body += "."
        return f"{idx}) {headline}: {body} ({source})"
    else:
        return f"{idx}) {headline} ({source})"


def format_date_es(dt: datetime) -> str:
    wd = WEEKDAYS_ES[dt.weekday()]
    month = MONTHS_ES[dt.month]
    return f"{wd}, {dt.day} de {month} de {dt.year}"


def build_cadena(articles: list[dict]) -> str:
    cadena_lines = []
    for a in articles[:4]:
        title = a.get("title", "").strip()
        preview = (a.get("preview") or "").strip()
        parts = [p.strip() for p in re.split(r'[.:]', title, maxsplit=1) if p.strip()]
        short_title = parts[0] if parts else title
        if preview and len(preview) >= 40:
            text = truncate_at_word(preview, 130)
        elif short_title:
            text = short_title[:130]
        else:
            text = title[:130]
        if not text.endswith((".", "!", "?")):
            text += "."
        cadena_lines.append(text)
    return "\n".join(cadena_lines[:4])


def main():
    parser = argparse.ArgumentParser(description="Generar pasquin Opción 6")
    parser.add_argument(
        "--limit", type=int, default=15,
        help="Cantidad de artículos (default: 15, max: 30)",
    )
    args = parser.parse_args()
    limit = min(max(args.limit, 1), 30)

    store = SqliteStore(DB_PATH)
    articles = store.get_articles(limit=limit)

    if not articles:
        print("No se encontraron artículos en la base de datos.")
        sys.exit(1)

    sections = {
        "DEPORTES": [],
        "ZONA OESTE": [],
        "NACIONALES": [],
        "INTERNACIONALES": [],
        "GENERAL": [],
    }

    for a in articles:
        sec = classify_article(a)
        sections.setdefault(sec, []).append(a)

    section_order = [
        "NACIONALES", "ZONA OESTE", "INTERNACIONALES",
        "DEPORTES", "GENERAL",
    ]

    now = datetime.now()
    date_str = format_date_es(now)

    lines = []
    lines.append(f"*INFORMATIVORAW — {date_str}*")
    lines.append("")

    global_idx = 0
    for sec_name in section_order:
        sec_articles = sections.get(sec_name, [])
        if not sec_articles:
            continue
        lines.append(f"*{sec_name}*")
        lines.append("")
        for a in sec_articles:
            global_idx += 1
            lines.append(format_article(global_idx, a))
        lines.append("")

    lines.append("*CADENA INFORMATIVA*")
    lines.append("")
    cadena = build_cadena(articles)
    lines.append(cadena)
    lines.append("")
    lines.append(
        "Reproducí esta información. Reenviála y conversala. "
        "Nueve de cada diez la están esperando."
    )
    lines.append("")
    lines.append("═══════════════════════════════════════")
    lines.append(
        f"InformativoRaw — {date_str} — Fuente: ~/noticias-raw/"
    )
    lines.append("")

    output = "\n".join(lines)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "borrador.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"✓ Pasquin generado: {out_path}")
    print(f"  Total artículos: {len(articles)}")
    for sec_name in section_order:
        sec_articles = sections.get(sec_name, [])
        if sec_articles:
            ids = [str(a["id"]) for a in sec_articles]
            print(f"  {sec_name}: {len(sec_articles)} artículos (IDs: {', '.join(ids)})")


if __name__ == "__main__":
    main()
