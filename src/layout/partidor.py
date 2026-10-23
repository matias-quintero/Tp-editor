"""Corte de un párrafo en líneas (word wrap)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

_PALABRA = re.compile(r"\S+")


@dataclass(frozen=True)
class Fragmento:
    """Una palabra (o trozo de palabra) ubicada dentro del párrafo."""

    inicio: int
    fin: int
    es_continuacion: bool = False


@dataclass(frozen=True)
class LineaPartida:
    """Resultado del corte: dónde empieza la línea y qué fragmentos tiene."""

    inicio: int
    fragmentos: tuple[Fragmento, ...]


@lru_cache(maxsize=8192)
def partir_parrafo(texto: str, ancho: int) -> tuple[LineaPartida, ...]:
    """Corta ``texto`` (sin saltos de línea) en líneas de a lo sumo ``ancho``.

    Regla: las palabras nunca se cortan, solo pasan a la línea siguiente.
    Única excepción inevitable: una palabra más larga que el ancho completo
    se parte en trozos de ``ancho`` caracteres.

    Siempre devuelve al menos una línea (un párrafo vacío es una línea vacía).
    El resultado depende solo de (texto, ancho), así que se cachea: al teclear
    solo se recalcula el párrafo que cambió.
    """
    if ancho < 1:
        raise ValueError("El ancho debe ser al menos 1")
    lineas: list[LineaPartida] = []
    actuales: list[Fragmento] = []
    largo = 0
    inicio_linea = 0
    for coincidencia in _PALABRA.finditer(texto):
        inicio, fin = coincidencia.span()
        if fin - inicio <= ancho:
            trozos = [Fragmento(inicio, fin)]
        else:
            trozos = [
                Fragmento(desde, min(desde + ancho, fin), desde > inicio)
                for desde in range(inicio, fin, ancho)
            ]
        for trozo in trozos:
            n = trozo.fin - trozo.inicio
            if actuales and largo + 1 + n > ancho:
                lineas.append(LineaPartida(inicio_linea, tuple(actuales)))
                actuales = []
                inicio_linea = trozo.inicio
            largo = n if not actuales else largo + 1 + n
            actuales.append(trozo)
    lineas.append(LineaPartida(inicio_linea, tuple(actuales)))
    return tuple(lineas)