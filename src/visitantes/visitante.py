"""Operaciones sobre el documento — patrón **Visitor**.

Roles del patrón (Gamma / Refactoring Guru):
    - Visitor:          ``Visitante``
    - ConcreteVisitor:  ``ContadorPalabras``, ``ContadorPaginas``,
                        ``ExportadorTextoPlano`` (y futuros exportadores)
    - Element:          ``ElementoDocumento`` (método ``aceptar``)
    - ConcreteElement:  ``Documento``, ``Pagina``, ``Parrafo``, ``Linea``, ``Palabra``
    - ObjectStructure:  el árbol Composite que arma ``Maquetador``
    - Client:           ``Editor`` (estadísticas) y ``ControladorConsola`` (exportar)
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.modelo.elementos import Documento, ElementoDocumento, Linea, Pagina, Palabra, Parrafo


class Visitante(ABC):
    """Visitor.

    Responsabilidad: declarar una operación de visita por cada tipo concreto
    de elemento del documento.

    Ítem de cambio que esconde: qué operaciones existen sobre el documento.
    Contar, exportar a otro formato, buscar, etc. se agregan como visitantes
    nuevos sin modificar las clases del modelo.
    """

    @abstractmethod
    def visitar_documento(self, documento: Documento) -> None: ...

    @abstractmethod
    def visitar_pagina(self, pagina: Pagina) -> None: ...

    @abstractmethod
    def visitar_parrafo(self, parrafo: Parrafo) -> None: ...

    @abstractmethod
    def visitar_linea(self, linea: Linea) -> None: ...

    @abstractmethod
    def visitar_palabra(self, palabra: Palabra) -> None: ...


class VisitanteRecursivo(Visitante):
    """Visitor base que recorre todo el árbol en preorden.

    Responsabilidad: implementar el recorrido por defecto, para que cada
    visitante concreto solo redefina los métodos que le interesan.

    Ítem de cambio que esconde: el orden de recorrido. Un visitante que no
    necesita bajar hasta las palabras (por ej. el contador de páginas)
    simplemente no llama a ``recorrer``.
    """

    def recorrer(self, elemento: ElementoDocumento) -> None:
        for hijo in elemento.hijos():
            hijo.aceptar(self)

    def visitar_documento(self, documento: Documento) -> None:
        self.recorrer(documento)

    def visitar_pagina(self, pagina: Pagina) -> None:
        self.recorrer(pagina)

    def visitar_parrafo(self, parrafo: Parrafo) -> None:
        self.recorrer(parrafo)

    def visitar_linea(self, linea: Linea) -> None:
        self.recorrer(linea)

    def visitar_palabra(self, palabra: Palabra) -> None:
        pass