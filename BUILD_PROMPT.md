# BUILD_PROMPT: Flujo `/pasquin` para el Build Agent

Este documento describe el flujo exacto para generar y publicar un pasquín
en `informativo-raw`. El build agent debe seguirlo al pie de la letra cuando
se invoca el comando `/pasquin`.

## Pipeline único

**NO usar `query.py`.** Todo se hace con `pasquin_data.py` como única fuente
de datos. Así se evita el bug de consultas divergentes.

```
pasquin_data.py (única fuente)
  ├── --limit N --json   → para mostrar disponibles
  └── --ids X,Y,Z --json → para generar el pasquin final
                              └── formatear_pasquin.py → stdout
```

## Paso a paso

### Paso 1 — Obtener disponibles

Usá el valor N que especificó el usuario. Si no especificó N, usá 20.

```bash
python3 ~/noticias-raw/pasquin_data.py --limit N --json --section-names specific 2>/dev/null
```

El flag `2>/dev/null` filtra logs de progreso (stderr).  
El JSON de salida tiene esta estructura:

```json
{
  "date": "martes 16/6/2026",
  "total_articles": 18,
  "sections": {
    "NACIONALES": [
      {
        "id": 102,
        "title": "Senado debate Ley Hojarasca",
        "preview": "El Senado buscará dictamen...",
        "source": "NA",
        "url": "https://..."
      }
    ],
    "PROVINCIAL / AMBA": [...],
    "INTERNACIONALES": [...],
    "ZONA OESTE": [...],
    "CLIMA": [...],
    "GENERAL": [...]
  }
}
```

### Paso 2 — Mostrar lista al usuario (OBLIGATORIO)

Parseá el JSON y mostrá los artículos agrupados por sección con este formato exacto:

```
📊 Noticias disponibles (N):

🇦🇷 NACIONALES
  [102] Senado debate Ley Hojarasca (NA)
  [105] Gobierno activa espadas para salvar a Adorni (LANACION)

🌐 INTERNACIONALES
  [201] Keiko Fujimori aumenta ventaja (BBCMUNDO)

📍 ZONA OESTE
  [301] 120 mil personas en fiesta patronal (ZOESTE)
```

Reglas:
- ID numérico entre corchetes: `[ID]`
- Título tal cual de la BD (recortar si muy largo con `...`)
- Fuente entre paréntesis: `(FUENTE)`
- Emoji de sección según corresponda (🇦🇷, 🌐, 📍, ⚽, ✅, 🌤️, 📰)
- Si una sección no tiene artículos, no la incluyas
- Mostrá TODAS las secciones que tengan artículos

### Paso 3 — Recibir selección

Preguntar:

```
¿Qué IDs incluís? (ej: "102,105,201" | "todos" | "solo nacionales")
```

Aceptar estos formatos de respuesta:

| Respuesta | Significado |
|---|---|
| `todos` | Todos los artículos mostrados |
| `102,105,201` | IDs específicos |
| `102-105,201` | Rango 102 a 105 + 201 |
| `solo nacionales` / `nacionales` | Solo sección NACIONALES |
| `nacionales,internacionales` | Combinación de secciones (por emoji o nombre) |

Si el usuario no entiende o pide aclaración, reformular amablemente.

### Paso 4 — Generar pasquin

```bash
python3 ~/noticias-raw/pasquin_data.py --ids 102,105,201 --json --section-names specific 2>/dev/null \
  | python3 ~/informativo-raw/formatear_pasquin.py
```

Esto produce texto en formato Telegram directo a stdout:

```
📰 INFORMATIVORAW — martes 16/6/2026

📢 CADENA: Senado debate Ley Hojarasca, Keiko Fujimori...

🇦🇷 NACIONALES

1) 🔹 SENADO DEBATE LEY HOJARASCA
El Senado buscará dictamen este miércoles...

2) 🔹 GOBIERNO ACTIVA ESPADAS POLÍTICAS
La Casa Rosada desplegó negociadores...

🌐 INTERNACIONALES

3) 🔹 KEIKO FUJIMORI AUMENTA VENTAJA EN PERÚ
Las autoridades electorales continúan...

FUENTES: BBCMUNDO, LANACION, NA

📢 Canal: t.me/+yzn1KN3WYsFjNTRh
```

> ⚠️ **No modificar este output.** Si el usuario quiere cambios (reordenar, sacar
> una noticia, cambiar título), volver a generar con otros IDs.

### Paso 5 — Mostrar y esperar aprobación

Mostrar el pasquin y preguntar:

```
¿Publico este pasquin en Telegram?
```

Solo cuando el usuario diga explícitamente "sí", "dale", "publicalo" o similar,
avanzar al paso 6.

### Paso 6 — Publicar

```bash
# Escribir el pasquin a borrador.txt
cat > ~/informativo-raw/borrador.txt << 'PASQUIN'
📰 INFORMATIVORAW — martes 16/6/2026
...
PASQUIN

# Publicar solo a Telegram
cd ~/informativo-raw && python3 publish.py --solo-telegram
```

## Reglas de oro

1. **Una sola fuente de datos:** `pasquin_data.py` para todo. `query.py` está prohibido para el flujo del pasquin.
2. **No publicar sin aprobación:** Mostrar primero, preguntar, esperar respuesta afirmativa explícita.
3. **No modificar el pipeline:** Si el usuario no gusta el resultado, regenerar con otros IDs. No editar el output de `formatear_pasquin.py` a mano.
4. **No guardar en borrador.txt hasta publicar:** El archivo `borrador.txt` solo se toca en el paso 6.
5. **No mezclar formatos:** El pasquin generado por el pipeline ya viene en formato Telegram correcto. No agregar caracteres ANCLA.

## Solución de problemas

| Problema | Causa | Solución |
|---|---|---|
| `pasquin_data.py` devuelve 0 artículos | No hay noticias recientes en la BD | Informar al usuario, sugerir `/scrape` primero |
| `formatear_pasquin.py` da error | JSON mal formado o vacío | Verificar que `pasquin_data.py --json` funcione solo |
| `publish.py --solo-telegram` da error de validación | El texto no empieza con `📰 INFORMATIVORAW` | Revisar que el pipeline haya corrido completo |
| El usuario dice IDs que no existen | IDs mal escritos o fuera de rango | Informar, pedir corrección |
