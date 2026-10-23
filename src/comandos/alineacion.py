"""Comando concreto que cambia la alineación."""

from __future__ import annotations

from src.alineacion.alineadores import Alineador
from src.comandos.comando import Comando
from src.edicion.editor import Editor


class ComandoCambiarAlineacion(Comando):
    """ConcreteCommand: cambia la estrategia de alineación del documento.

    Es además el Client del patrón Strategy: elige qué ``Alineador`` usar.

    Responsabilidad: aplicar la nueva alineación y recordar la anterior para
    que CTRL+Z también deshaga cambios de alineación.

    Ítem de cambio que esconde: cómo se revierte un cambio de formato.
    """

    def __init__(self, editor: Editor, alineador: Alineador) -> None:
        self._editor = editor
        self._nuevo = alineador
        self._anterior: Alineador | None = None

    def ejecutar(self) -> bool:
        if self._editor.alineador == self._nuevo:
            return False
        self._anterior = self._editor.cambiar_alineador(self._nuevo)
        return True

    def deshacer(self) -> None:
        if self._anterior is not None:
            self._editor.cambiar_alineador(self._anterior)