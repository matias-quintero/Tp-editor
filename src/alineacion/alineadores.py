"""Alineación del texto — patrón **Strategy**.

Roles del patrón (Gamma / Refactoring Guru):
    - Strategy:          ``Alineador``
    - ConcreteStrategy:  ``AlineadorIzquierda``, ``AlineadorDerecha``,
                         ``AlineadorCentrado``, ``AlineadorJustificado``
    - Context:           ``Maquetador`` (layout/maquetador.py), que guarda la
                         estrategia actual y le delega el cálculo de columnas
    - Client:            ``ComandoCambiarAlineacion``, que elige la estrategia

Cada estrategia solo responde una pregunta: dadas las longitudes de las
palabras de una línea y el ancho, ¿en qué columna empieza cada palabra?
No dibuja ni conoce al modelo, por eso es trivial de testear.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar, Sequence


class Alineador(ABC):
    """Strategy.

    Responsabilidad: decidir en qué columna empieza cada palabra de una línea.

    Ítem de cambio que esconde: el algoritmo de alineación. Agregar una
    alineación nueva es agregar una subclase, sin tocar el maquetador.
    """

    nombre: ClassVar[str]

    @abstractmethod
    def columnas(self, longitudes: Sequence[int], ancho: int, es_ultima: bool) -> list[int]:
        """Columna inicial de cada palabra.

        ``es_ultima`` indica si es la última línea del párrafo (la
        justificación no la estira, como en cualquier procesador de texto).
        Se asume que las palabras entran en el ancho separadas por un espacio.
        """

    def columna_vacia(self, ancho: int) -> int:
        """Columna donde se dibuja el cursor en una línea sin palabras."""
        return self.columnas([0], ancho, True)[0]

    def __eq__(self, otro: object) -> bool:
        return type(self) is type(otro)

    def __hash__(self) -> int:
        return hash(type(self))


def _consecutivas(longitudes: Sequence[int], inicio: int) -> list[int]:
    """Columnas de palabras separadas por un único espacio desde ``inicio``."""
    columnas: list[int] = []
    columna = inicio
    for largo in longitudes:
        columnas.append(columna)
        columna += largo + 1
    return columnas


def _ocupado(longitudes: Sequence[int]) -> int:
    """Ancho que ocupan las palabras separadas por un espacio."""
    return sum(longitudes) + max(0, len(longitudes) - 1)


class AlineadorIzquierda(Alineador):
    """ConcreteStrategy: texto pegado al margen izquierdo."""

    nombre = "Izquierda"

    def columnas(self, longitudes: Sequence[int], ancho: int, es_ultima: bool) -> list[int]:
        return _consecutivas(longitudes, 0)


class AlineadorDerecha(Alineador):
    """ConcreteStrategy: texto pegado al margen derecho."""

    nombre = "Derecha"

    def columnas(self, longitudes: Sequence[int], ancho: int, es_ultima: bool) -> list[int]:
        return _consecutivas(longitudes, max(0, ancho - _ocupado(longitudes)))


class AlineadorCentrado(Alineador):
    """ConcreteStrategy: texto centrado (el sobrante impar va a la derecha)."""

    nombre = "Centrado"

    def columnas(self, longitudes: Sequence[int], ancho: int, es_ultima: bool) -> list[int]:
        return _consecutivas(longitudes, max(0, (ancho - _ocupado(longitudes)) // 2))


class AlineadorJustificado(Alineador):
    """ConcreteStrategy: reparte los espacios para llenar todo el ancho.

    La última línea del párrafo y las líneas de una sola palabra se alinean
    a la izquierda. Si los espacios no se reparten exacto, los huecos de la
    izquierda reciben uno más.
    """

    nombre = "Justificado"

    def columnas(self, longitudes: Sequence[int], ancho: int, es_ultima: bool) -> list[int]:
        if es_ultima or len(longitudes) <= 1:
            return _consecutivas(longitudes, 0)
        huecos = len(longitudes) - 1
        espacio_libre = max(huecos, ancho - sum(longitudes))
        base, extra = divmod(espacio_libre, huecos)
        columnas: list[int] = []
        columna = 0
        for i, largo in enumerate(longitudes):
            columnas.append(columna)
            columna += largo + base + (1 if i < extra else 0)
        return columnas