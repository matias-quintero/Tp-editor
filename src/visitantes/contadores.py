"""Visitantes concretos para estadísticas del documento."""

from __future__ import annotations

from src.modelo.elementos import Documento, Pagina, Palabra
from src.visitantes.visitante import VisitanteRecursivo


class ContadorPalabras(VisitanteRecursivo):
    """ConcreteVisitor: cuenta las palabras del documento.

    Responsabilidad: acumular la cantidad de palabras recorriendo hasta las hojas.

    Ítem de cambio que esconde: qué cuenta como palabra para la estadística
    (los trozos de una palabra larga partida no suman de nuevo).
    """

    def __init__(self) -> None:
        self.total = 0

    def visitar_palabra(self, palabra: Palabra) -> None:
        if not palabra.es_continuacion:
            self.total += 1

    @classmethod
    def contar(cls, documento: Documento) -> int:
        visitante = cls()
        documento.aceptar(visitante)
        return visitante.total


class ContadorPaginas(VisitanteRecursivo):
    """ConcreteVisitor: cuenta las páginas del documento.

    Responsabilidad: acumular la cantidad de páginas; no baja más allá de
    ellas porque no le hace falta.

    Ítem de cambio que esconde: el criterio de qué es una página contable.
    """

    def __init__(self) -> None:
        self.total = 0

    def visitar_pagina(self, pagina: Pagina) -> None:
        self.total += 1  # no recorre los hijos: no los necesita

    @classmethod
    def contar(cls, documento: Documento) -> int:
        visitante = cls()
        documento.aceptar(visitante)
        return visitante.total