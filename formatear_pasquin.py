#!/usr/bin/env python3
"""Formatea JSON de pasquin_data.py a texto Telegram.

Usage:
  python3 ../noticias-raw/pasquin_data.py --limit 15 --json | python3 formatear_pasquin.py > borrador.txt
  python3 publish.py
"""

import json
import sys
from datetime import datetime

TELEGRAM_MAX = 4096
CANAL_LINK = "t.me/+yzn1KN3WYsFjNTRh"

SECTION_EMOJIS = {
    "NACIONALES": "\U0001f1e6\U0001f1f7",
    "PROVINCIAL_AMBA": "\U0001f4cd",
    "INTERNACIONALES": "\U0001f310",
    "ZONA OESTE": "\U0001f4cd",
    "LOCALES": "\U0001f4cd",
    "DEPORTES": "\u26bd",
    "VERIFICACION": "\u2705",
    "CLIMA": "\U0001f324\ufe0f",
    "GENERAL": "\U0001f4f0",
}

SECTION_ORDER = [
    "NACIONALES", "PROVINCIAL_AMBA", "INTERNACIONALES",
    "ZONA OESTE", "LOCALES", "DEPORTES", "VERIFICACION",
    "CLIMA", "GENERAL",
]

FOOTER = f"\n\U0001f4e2 Canal: {CANAL_LINK}"


def _markers(a: dict) -> str:
    m = []
    if a.get("_propaganda"):
        m.append("\u26a0\ufe0f")
    if a.get("_desmentido"):
        m.append("\u274c")
    elif a.get("_chequeado_ref"):
        m.append("\u2705")
    return " " + " ".join(m) if m else ""


def _truncar(texto: str, max_len: int) -> str:
    if len(texto) <= max_len:
        return texto
    return texto[: max_len - 3].rsplit(" ", 1)[0] + "..."


def _dia_semana(dt: datetime) -> str:
    dias = ["lunes", "martes", "mi\u00e9rcoles", "jueves", "viernes", "s\u00e1bado", "domingo"]
    return dias[dt.weekday()]


def _format_fecha(dt: datetime) -> str:
    meses = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    return f"{_dia_semana(dt)} {dt.day}/{dt.month}/{dt.year}"


INTERNAL_SECTIONS = [
    "NACIONALES", "PROVINCIAL_AMBA", "INTERNACIONALES",
    "ZONA OESTE", "LOCALES", "DEPORTES", "VERIFICACION",
    "CLIMA", "GENERAL",
]

def _claves_seccion(sections: dict) -> dict[str, str]:
    """Mapea claves internas a las claves reales del JSON (display names).
    Ej: PROVINCIAL_AMBA → 'PROVINCIAL / AMBA' si existe en el JSON."""
    registry: dict[str, str] = {}
    for sk in sections:
        normalized = sk.upper().replace(" / ", "_").replace(" ", "_").replace("/", "_")
        registry[normalized] = sk
    m = {}
    for k in INTERNAL_SECTIONS:
        if k in sections:
            m[k] = k
        elif k in registry:
            m[k] = registry[k]
        else:
            m[k] = k
    return m


def _generar_cadena(data: dict) -> str:
    partes = []
    sections = data.get("sections", {})
    claves = _claves_seccion(sections)
    for sec in ["NACIONALES", "INTERNACIONALES", "PROVINCIAL_AMBA"]:
        arts = sections.get(claves.get(sec, sec), [])
        for a in arts[:1]:
            t = (a.get("title") or "").strip()
            t = t.split(":", 1)[0] if ":" in t else t
            t = t.strip("\"'")
            if t and len(t) > 15:
                partes.append(_truncar(t, 80))
            break
    if not partes:
        return ""
    cadena = ", ".join(partes[:3])
    return cadena[:297]


def formatear(data: dict) -> str:
    now = datetime.now()

    header = f"\U0001f4f0 INFORMATIVORAW \u2014 {_format_fecha(now)}"
    cadena = _generar_cadena(data)
    cadena_block = f"\U0001f4e2 CADENA: {cadena}" if cadena else ""

    items = []
    source_set = set()
    tiene_deportes_arg = False
    seen_sections: set[str] = set()
    sections = data.get("sections", {})
    claves = _claves_seccion(sections)

    for sec in SECTION_ORDER:
        sec_real = claves.get(sec, sec)
        if sec_real in seen_sections:
            continue
        seen_sections.add(sec_real)
        articulos = sections.get(sec_real, [])
        if not articulos:
            continue

        if sec == "DEPORTES":
            for a in articulos:
                t = (a.get("title") or "").lower()
                if any(k in t for k in ["argentina", "argentin", "selecci\u00f3n", "colapinto",
                                          "boca", "river", "racing", "independiente"]):
                    tiene_deportes_arg = True
                    break
            if not tiene_deportes_arg:
                continue

        items.append(("section", sec, sec_real, articulos))

    clima_arts = sections.get(claves.get("CLIMA", "CLIMA"), [])
    clima_line = ""
    if clima_arts:
        clima = clima_arts[0]
        ct = (clima.get("title") or "").strip()
        cp = (clima.get("preview") or "").strip()
        clima_line = cp if cp and len(cp) > 20 else ct
        if clima_line:
            source_set.add(clima.get("source", "").upper())

    max_preview = 280
    while True:
        lines = []
        source_set.clear()
        count = 0
        total = len(header) + 1

        lines.append(header)

        if cadena_block:
            total += 1 + len(cadena_block) + 1
            lines.append("")
            lines.append(cadena_block)
            lines.append("")

        for _type, sec, sec_real, articulos in items:
            emoji = SECTION_EMOJIS.get(sec, "\U0001f4f0")
            sec_line = f"{emoji} {sec_real}"
            header_cost = 1 + len(sec_line) + 1

            if total + header_cost >= TELEGRAM_MAX - 200:
                break

            sec_lines = [sec_line, ""]
            sec_len = header_cost
            added = False

            for a in articulos:
                if a.get("_es_clima"):
                    continue
                count += 1
                title = (a.get("title") or "").strip().upper()
                title = _truncar(title, 120)
                preview = (a.get("preview") or "").strip()
                is_note = a.get("_note", False)
                markers = _markers(a) if not is_note else ""

                prefix = "\U0001f4dd" if is_note else "\U0001f539"
                item_line = f"{count}) {prefix} {title}{markers}"
                item_len = len(item_line) + 1

                pl = ""
                if preview and len(preview) > 20:
                    pl = _truncar(preview, max_preview)
                    item_len += len(pl) + 1

                item_len += 1

                if total + sec_len + item_len >= TELEGRAM_MAX - 200:
                    break

                if not is_note:
                    source_set.add(a.get("source", "").upper())
                sec_lines.append(item_line)
                sec_len += len(item_line) + 1
                if pl:
                    sec_lines.append(pl)
                    sec_len += len(pl) + 1
                sec_lines.append("")
                sec_len += 1
                added = True

            if added:
                total += sec_len
                lines.extend(sec_lines)

        if clima_line:
            cl = f"\U0001f324\ufe0f {_truncar(clima_line, 200)}"
            if total + 1 + len(cl) < TELEGRAM_MAX - 200:
                total += 1 + len(cl) + 1
                lines.append("")
                lines.append(cl)

        fuentes = ""
        if source_set:
            fuentes = f"FUENTES: {', '.join(sorted(source_set))}"

        footer_len = len(FOOTER) + (1 + len(fuentes) if fuentes else 0)

        if total + footer_len <= TELEGRAM_MAX:
            if fuentes:
                lines.append("")
                lines.append(fuentes)
            lines.append(FOOTER)
            return "\n".join(lines)

        max_preview -= 20
        if max_preview < 40:
            max_preview = 40
            if fuentes:
                # Drop fuentes
                footer_len = len(FOOTER)
                if total + footer_len <= TELEGRAM_MAX:
                    lines.append(FOOTER)
                    return "\n".join(lines)
                break
            break

    return "\n".join(lines)


def main():
    data = json.load(sys.stdin)
    texto = formatear(data)
    sys.stdout.write(texto)
    sys.stdout.write("\n")
    sys.stderr.write(f"Pasquin: {len(texto)} caracteres\n")
    if len(texto) > TELEGRAM_MAX:
        sys.stderr.write(f"\u26a0 Advertencia: excede {TELEGRAM_MAX} chars ({len(texto)})\n")
    else:
        sys.stderr.write(f"\u2713 Cabe en 1 mensaje de Telegram ({TELEGRAM_MAX - len(texto)} libres)\n")


if __name__ == "__main__":
    main()
