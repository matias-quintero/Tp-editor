"""Comandos concretos que modifican el texto."""

from __future__ import annotations

from src.comandos.comando import Comando
from src.edicion.editor import Editor


class ComandoInsertar(Comando):
    """ConcreteCommand: inserta texto en la posición actual del cursor.

    Responsabilidad: insertar y recordar dónde y cuánto se insertó.

    Ítem de cambio que esconde: cómo se revierte una inserción.
    """

    def __init__(self, editor: Editor, texto: str) -> None:
        self._editor = editor
        self._texto = texto
        self._posicion = 0

    def ejecutar(self) -> bool:
        if not self._texto:
            return False
        self._posicion = self._editor.cursor.posicion
        self._editor.insertar(self._posicion, self._texto)
        return True

    def deshacer(self) -> None:
        self._editor.borrar(self._posicion, len(self._texto))


class ComandoBorrar(Comando):
    """ConcreteCommand: borra un carácter respecto del cursor.

    Con ``hacia_atras=True`` se comporta como Backspace (borra el carácter
    anterior al cursor); con ``False``, como Supr (borra el siguiente).

    Responsabilidad: borrar y recordar el carácter borrado y la posición
    del cursor previa.

    Ítem de cambio que esconde: la diferencia entre Backspace y Supr y cómo
    se restaura el cursor al deshacer.
    """

    def __init__(self, editor: Editor, hacia_atras: bool = True) -> None:
        self._editor = editor
        self._hacia_atras = hacia_atras
        self._inicio = 0
        self._borrado = ""
        self._cursor_previo = 0

    def ejecutar(self) -> bool:
        posicion = self._editor.cursor.posicion
        if self._hacia_atras:
            if posicion == 0:
                return False
            inicio = posicion - 1
        else:
            if posicion >= len(self._editor.texto):
                return False
            inicio = posicion
        self._cursor_previo = posicion
        self._inicio = inicio
        self._borrado = self._editor.borrar(inicio, 1)
        return True

    def deshacer(self) -> None:
        self._editor.insertar(self._inicio, self._borrado)
        self._editor.mover_cursor_a(self._cursor_previo)