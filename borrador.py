#!/usr/bin/env python3
"""Genera un pasquin Opcion 6 desde noticias-raw.
Reglas: /pasquin original — NO alucinar, solo datos de la BD."""

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

NON_ARGENTINE_SOURCES = {"AP", "EFE", "REUTERS", "AFP", "DPA", "EUROPAPRESS"}

WEEKDAYS_ES = [
    "lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo",
]
MONTHS_ES = [
    "", "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

# Palabras/claves que indican contenido no-noticia
JUNK_TITLE_PATTERNS = re.compile(
    r"^(clima|pronostico|efemeride|escriben hoy|horoscopo|"
    r"la palabra del dia|la frase del dia|feliz|"
    r"que paso un dia como hoy|a que hay que estar atentos|"
    r"el tiempo |neblinas|lluvias|tormenta|soleado|nubosidad|"
    r"\d{1,2} de \w+ de \d{4})",
    re.I,
)
# Titulos que son solo listas de nombres (separados por |)
JUNK_LIST_PATTERN = re.compile(r"\|")
# Titulos muy cortos sin preview
JUNK_SHORT_TITLE = 25


def formato_fecha_es(dt: datetime) -> str:
    wd = WEEKDAYS_ES[dt.weekday()]
    return f"{wd}, {dt.day} de {MONTHS_ES[dt.month]} de {dt.year}"


def es_articulo_valido(articulo: dict) -> bool:
    titulo = (articulo.get("title") or "").strip()
    preview = (articulo.get("preview") or "").strip()
    source = articulo.get("source", "").upper()

    if not titulo or len(titulo) < JUNK_SHORT_TITLE:
        return False

    if JUNK_TITLE_PATTERNS.match(titulo.lower()):
        return False

    # Listas de nombres (columnistas, firmas) sin preview
    if not preview and JUNK_LIST_PATTERN.search(titulo):
        return False

    # EUROPAPRESS: solo politica/conflictos internacionales, no tecnologia/autos/economia
    if source == "EUROPAPRESS":
        cls = _parse_classification(articulo)
        categoria = (cls.get("topic", {}).get("categoria") or "").lower()
        if not any(k in categoria for k in ["politica", "geopolitica", "conflicto"]):
            return False

    return True


def _parse_classification(articulo: dict) -> dict:
    raw = articulo.get("classification", "{}")
    if not raw or raw.strip() == "{}":
        return {}
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}


def clasificar_articulo(articulo: dict) -> str:
    source = articulo.get("source", "").upper()

    if source in ZONA_OESTE_SOURCES:
        return "ZONA OESTE"

    if source in NON_ARGENTINE_SOURCES:
        return "INTERNACIONALES"

    cls = _parse_classification(articulo)
    categoria = (cls.get("topic", {}).get("categoria") or "").lower()
    geo = cls.get("geo", {})
    partido = (geo.get("partido") or geo.get("localidad") or "").strip()

    if "deporte" in categoria:
        return "DEPORTES"

    if partido in {
        "Moron", "Ituzaingo", "Merlo", "Hurlingham", "Castelar", "Haedo",
        "Villa Tesei", "Libertad", "El Palomar", "Ramos Mejia", "San Justo",
        "La Tablada", "Lomas del Mirador", "Villa Luzuriaga", "Rafael Castillo",
        "Gonzalez Catan", "Isidro Casanova", "Ciudad Evita", "Tapiales",
        "Aldo Bonzi",
    }:
        return "ZONA OESTE"

    if source in SOURCES:
        return "NACIONALES"

    return "GENERAL"


def formatear_articulo(idx: int, articulo: dict) -> str:
    titulo = (articulo.get("title") or "").strip()
    preview = (articulo.get("preview") or "").strip()
    source = articulo.get("source", "")

    # Si preview < 100 caracteres, se considera incompleto → solo titulo
    if preview and len(preview) >= 100:
        preview = preview.strip()
        if not preview.endswith((".", "!", "?")):
            preview += "."
        return f"{idx}) {titulo}: {preview} ({source})"
    else:
        return f"{idx}) {titulo} ({source})"


def armar_cadena(sections: dict) -> str:
    """3-4 lineas con hechos clave. Prioriza NACIONALES + INTERNACIONALES."""
    prioridad = []
    for sec in ["NACIONALES", "INTERNACIONALES", "ZONA OESTE", "DEPORTES"]:
        prioridad.extend(sections.get(sec, []))

    headlines = []
    for a in prioridad:
        titulo = (a.get("title") or "").strip()
        # Si el titulo tiene ":", usar la parte de la izquierda
        partes = [p.strip() for p in titulo.split(":", 1) if p.strip()]
        hl = partes[0] if len(partes) > 1 else titulo
        hl = hl.strip().strip("\"'")
        if hl and 20 < len(hl) < 150:
            headlines.append(hl)
            if len(headlines) >= 4:
                break

    if not headlines:
        return ""

    lines = []
    for h in headlines:
        if not h.endswith((".", "!", "?")):
            h += "."
        lines.append(h)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generar pasquin Opcion 6")
    parser.add_argument(
        "--limit", type=int, default=15,
        help="Cantidad de articulos a procesar (default: 15, max: 30)",
    )
    args = parser.parse_args()
    limit = min(max(args.limit, 1), 30)

    store = SqliteStore(DB_PATH)
    raw_articles = store.get_articles(limit=limit * 2)

    articles = [a for a in raw_articles if es_articulo_valido(a)][:limit]

    if not articles:
        print("No se encontraron articulos validos en la base de datos.")
        sys.exit(1)

    sections = {
        "NACIONALES": [],
        "ZONA OESTE": [],
        "INTERNACIONALES": [],
        "DEPORTES": [],
        "GENERAL": [],
    }

    for a in articles:
        sec = clasificar_articulo(a)
        sections.setdefault(sec, []).append(a)

    section_order = [
        "NACIONALES", "ZONA OESTE", "INTERNACIONALES",
        "DEPORTES", "GENERAL",
    ]

    now = datetime.now()
    date_str = formato_fecha_es(now)

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
            lines.append(formatear_articulo(global_idx, a))
        lines.append("")

    # Cadena informativa
    cadena = armar_cadena(sections)
    if cadena:
        lines.append("*CADENA INFORMATIVA*")
        lines.append("")
        lines.append(cadena)
        lines.append("")
        lines.append(
            "Reproduci esta informacion. Reenviala y conversala. "
            "Nueve de cada diez la estan esperando."
        )
        lines.append("")

    lines.append("═══════════════════════════════════════")
    lines.append(f"InformativoRaw — {date_str} — Fuente: ~/noticias-raw/")
    lines.append("")

    output = "\n".join(lines)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "borrador.txt")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"* Pasquin generado: {out_path}")
    print(f"  Total articulos: {len(articles)} ({len(raw_articles) - len(articles)} filtrados)")
    for sec_name in section_order:
        sec_articles = sections.get(sec_name, [])
        if sec_articles:
            ids = [str(a["id"]) for a in sec_articles]
            print(f"  {sec_name}: {len(sec_articles)} articulos (IDs: {', '.join(ids)})")


if __name__ == "__main__":
    main()
