"""Historial de comandos para deshacer (Invoker del Command)."""

from __future__ import annotations

from collections import deque

from src.comandos.comando import Comando


class HistorialComandos:
    """Invoker del patrón Command.

    Responsabilidad: ejecutar comandos y apilar los que tuvieron efecto para
    poder deshacerlos en orden inverso (CTRL+Z).

    Ítem de cambio que esconde: la política del historial (pila con un
    límite de tamaño; si se llena se descartan los más viejos). Agregar
    "rehacer" sería tocar solo esta clase.
    """

    def __init__(self, limite: int = 10000) -> None:
        self._pila: deque[Comando] = deque(maxlen=limite)

    def ejecutar(self, comando: Comando) -> bool:
        if comando.ejecutar():
            self._pila.append(comando)
            return True
        return False

    def deshacer(self) -> bool:
        if not self._pila:
            return False
        self._pila.pop().deshacer()
        return True

    @property
    def puede_deshacer(self) -> bool:
        return bool(self._pila)

    def __len__(self) -> int:
        return len(self._pila)