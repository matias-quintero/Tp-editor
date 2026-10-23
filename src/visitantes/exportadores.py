"""Exportadores del documento (visitantes concretos)."""

from __future__ import annotations

from abc import abstractmethod
from typing import ClassVar

from src.modelo.elementos import Documento, Linea, Pagina
from src.visitantes.visitante import VisitanteRecursivo


class Exportador(VisitanteRecursivo):
    """Visitor base para exportar a un formato.

    Responsabilidad: definir la interfaz común de todos los exportadores
    (``exportar`` y la extensión de archivo sugerida).

    Ítem de cambio que esconde: el formato de salida. Para exportar a HTML,
    Markdown, etc. se agrega una subclase; el modelo y el editor no cambian.
    """

    extension: ClassVar[str]

    def exportar(self, documento: Documento) -> str:
        self._reiniciar()
        documento.aceptar(self)
        return self._resultado()

    @abstractmethod
    def _reiniciar(self) -> None: ...

    @abstractmethod
    def _resultado(self) -> str: ...


class ExportadorTextoPlano(Exportador):
    """ConcreteVisitor: exporta a texto plano respetando ancho, alineación y páginas.

    Responsabilidad: producir el mismo texto que se ve en la consola, con
    un separador entre páginas.

    Ítem de cambio que esconde: el formato del archivo .txt (separador de
    página, fin de línea).
    """

    extension = ".txt"

    def __init__(self) -> None:
        self._lineas: list[str] = []
        self._ancho = 0

    def _reiniciar(self) -> None:
        self._lineas = []

    def _resultado(self) -> str:
        return "\n".join(self._lineas) + "\n"

    def visitar_documento(self, documento: Documento) -> None:
        self._ancho = documento.ancho
        self.recorrer(documento)

    def visitar_pagina(self, pagina: Pagina) -> None:
        if pagina.numero > 1:
            self._lineas.append(f" Página {pagina.numero} ".center(self._ancho, "-"))
        self.recorrer(pagina)

    def visitar_linea(self, linea: Linea) -> None:
        self._lineas.append(linea.renderizar())  # no necesita bajar a las palabras