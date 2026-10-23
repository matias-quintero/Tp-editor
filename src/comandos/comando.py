"""Acciones deshacibles — patrón **Command**.

Roles del patrón (Gamma / Refactoring Guru):
    - Command:          ``Comando``
    - ConcreteCommand:  ``ComandoInsertar``, ``ComandoBorrar``, ``ComandoCambiarAlineacion``
    - Receiver:         ``Editor`` (edicion/editor.py)
    - Invoker:          ``HistorialComandos``, que ejecuta los comandos y los
                        guarda para poder deshacerlos con CTRL+Z
    - Client:           ``ControladorConsola`` (vista/controlador.py), que crea
                        el comando adecuado según la tecla presionada
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class Comando(ABC):
    """Command.

    Responsabilidad: encapsular una modificación del documento junto con la
    información necesaria para revertirla.

    Ítem de cambio que esconde: qué datos hay que guardar para deshacer cada
    tipo de acción (lo borrado, la posición, la alineación anterior...).
    """

    @abstractmethod
    def ejecutar(self) -> bool:
        """Aplica el cambio. Devuelve ``False`` si no tuvo efecto (por ejemplo,
        borrar al principio del documento), y en ese caso no se guarda en el
        historial."""

    @abstractmethod
    def deshacer(self) -> None:
        """Revierte el cambio dejando documento y cursor como estaban."""