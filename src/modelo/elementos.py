"""Modelo del documento — patrón **Composite**.

Un documento se representa como un árbol:

    Documento -> Pagina -> Parrafo -> Linea -> Palabra

Roles del patrón (Gamma / Refactoring Guru):
    - Component: ``ElementoDocumento``
    - Composite: ``ElementoCompuesto`` (base) y sus subclases ``Documento``,
      ``Pagina``, ``Parrafo`` y ``Linea``
    - Leaf:      ``Palabra``
    - Client:    el maquetador (que arma el árbol) y los visitantes (que lo recorren)

El árbol es una *vista* del texto: lo construye ``Maquetador`` a partir del
texto plano del editor cada vez que este cambia. Por eso los nodos no se
modifican después de armados.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar, Generic, Sequence, TypeVar

if TYPE_CHECKING:
    from src.visitantes.visitante import Visitante


class ElementoDocumento(ABC):
    """Component del Composite.

    Responsabilidad: definir la interfaz común a todas las partes del
    documento (obtener sus hijos, su texto y aceptar visitantes), para que
    los clientes traten igual a una palabra que a un documento entero.

    Ítem de cambio que esconde: la profundidad y la forma concreta del árbol.
    Si mañana se agrega un nivel (por ej. "Sección" entre página y párrafo),
    los clientes que recorren ``hijos()`` o usan ``aceptar`` no cambian.
    """

    @abstractmethod
    def hijos(self) -> Sequence[ElementoDocumento]:
        """Partes que componen a este elemento (vacío para las hojas)."""

    @abstractmethod
    def texto(self) -> str:
        """Texto plano contenido en el elemento."""

    @abstractmethod
    def aceptar(self, visitante: Visitante) -> None:
        """Punto de entrada del patrón Visitor (double dispatch)."""


H = TypeVar("H", bound=ElementoDocumento)


class ElementoCompuesto(ElementoDocumento, Generic[H]):
    """Composite genérico.

    Responsabilidad: guardar y exponer la lista ordenada de hijos y
    componer el texto a partir del de ellos.

    Ítem de cambio que esconde: cómo se almacenan los hijos (hoy una lista)
    y cómo se une su texto (cada subclase define su separador).
    """

    SEPARADOR: ClassVar[str] = ""

    def __init__(self, hijos: Sequence[H] | None = None) -> None:
        self._hijos: list[H] = list(hijos) if hijos is not None else []

    def agregar(self, hijo: H) -> None:
        self._hijos.append(hijo)

    def hijos(self) -> Sequence[H]:
        return self._hijos

    def texto(self) -> str:
        return self.SEPARADOR.join(hijo.texto() for hijo in self._hijos)


class Palabra(ElementoDocumento):
    """Leaf del Composite.

    Responsabilidad: representar una palabra (secuencia sin espacios) y
    recordar en qué posición del párrafo empieza, para poder ubicar el cursor.

    Ítem de cambio que esconde: qué se considera "palabra". Si una palabra
    es más larga que el ancho de línea es imposible no cortarla; en ese caso
    se parte en trozos y los trozos que no son el primero quedan marcados
    con ``es_continuacion`` para no contarlos como palabras nuevas.
    """

    def __init__(self, texto: str, inicio: int, es_continuacion: bool = False) -> None:
        self._texto = texto
        self.inicio = inicio  # offset relativo al inicio del párrafo
        self.es_continuacion = es_continuacion

    @property
    def fin(self) -> int:
        """Offset (relativo al párrafo) inmediatamente después de la palabra."""
        return self.inicio + len(self._texto)

    def __len__(self) -> int:
        return len(self._texto)

    def hijos(self) -> Sequence[ElementoDocumento]:
        return ()

    def texto(self) -> str:
        return self._texto

    def aceptar(self, visitante: Visitante) -> None:
        visitante.visitar_palabra(self)


class Linea(ElementoCompuesto[Palabra]):
    """Composite: una línea visual de ancho fijo.

    Responsabilidad: conocer sus palabras y la columna en la que se dibuja
    cada una (calculada por la estrategia de alineación), y a partir de eso
    renderizarse y traducir una posición del texto a una columna de pantalla.

    Ítem de cambio que esconde: cómo se traduce un offset del texto a una
    columna visual cuando la alineación agrega o quita espacios.
    """

    SEPARADOR = " "

    def __init__(
        self,
        palabras: Sequence[Palabra],
        columnas: Sequence[int],
        ancho: int,
        inicio: int,
        columna_vacia: int = 0,
    ) -> None:
        super().__init__(palabras)
        if len(palabras) != len(columnas):
            raise ValueError("Debe haber una columna por palabra")
        self._columnas = list(columnas)
        self.ancho = ancho
        self.inicio = inicio  # offset relativo al párrafo donde empieza la línea
        self._columna_vacia = columna_vacia

    @property
    def columnas(self) -> Sequence[int]:
        return self._columnas

    def renderizar(self) -> str:
        """Texto de la línea con los espacios que pide la alineación."""
        partes: list[str] = []
        largo = 0
        for palabra, columna in zip(self._hijos, self._columnas):
            partes.append(" " * (columna - largo))
            partes.append(palabra.texto())
            largo = columna + len(palabra)
        return "".join(partes)

    def columna_de(self, offset: int) -> int:
        """Columna de pantalla para un offset relativo al párrafo."""
        palabras = self._hijos
        if not palabras:
            return self._columna_vacia
        for i, palabra in enumerate(palabras):
            if offset < palabra.inicio:
                if i == 0:  # espacios al inicio del párrafo
                    return max(0, self._columnas[0] - (palabra.inicio - offset))
                anterior = palabras[i - 1]
                columna = self._columnas[i - 1] + len(anterior) + (offset - anterior.fin)
                return min(columna, self._columnas[i] - 1)
            if offset <= palabra.fin:
                return self._columnas[i] + (offset - palabra.inicio)
        ultima = palabras[-1]
        columna = self._columnas[-1] + len(ultima) + (offset - ultima.fin)
        return min(columna, self.ancho)

    def aceptar(self, visitante: Visitante) -> None:
        visitante.visitar_linea(self)


class Parrafo(ElementoCompuesto[Linea]):
    """Composite: un párrafo (texto entre dos saltos de línea).

    Responsabilidad: agrupar las líneas de un párrafo y recordar dónde
    empieza en el texto completo.

    Ítem de cambio que esconde: que un párrafo puede quedar partido entre
    dos páginas. En ese caso cada página tiene su propio fragmento y los
    fragmentos posteriores al primero se marcan con ``es_continuacion``.
    """

    SEPARADOR = "\n"

    def __init__(self, inicio: int, es_continuacion: bool = False) -> None:
        super().__init__()
        self.inicio = inicio  # offset absoluto en el texto del editor
        self.es_continuacion = es_continuacion

    def aceptar(self, visitante: Visitante) -> None:
        visitante.visitar_parrafo(self)


class Pagina(ElementoCompuesto[Parrafo]):
    """Composite: una página con una cantidad fija de líneas.

    Responsabilidad: agrupar los párrafos (o fragmentos) que entran en ella
    y conocer su número.

    Ítem de cambio que esconde: el criterio de corte de página (lo decide el
    maquetador; la página solo guarda el resultado).
    """

    SEPARADOR = "\n"

    def __init__(self, numero: int) -> None:
        super().__init__()
        self.numero = numero

    def aceptar(self, visitante: Visitante) -> None:
        visitante.visitar_pagina(self)


class Documento(ElementoCompuesto[Pagina]):
    """Composite raíz.

    Responsabilidad: ser la raíz del árbol y guardar los parámetros con los
    que se maquetó (ancho de línea y nombre de la alineación).

    Ítem de cambio que esconde: la configuración de maquetado; los
    exportadores la leen de acá sin conocer al maquetador.
    """

    SEPARADOR = "\n"

    def __init__(self, ancho: int, alineacion: str) -> None:
        super().__init__()
        self.ancho = ancho
        self.alineacion = alineacion

    def aceptar(self, visitante: Visitante) -> None:
        visitante.visitar_documento(self)