"""Manejo de la terminal: modo raw, pantalla alternativa y escritura."""

from __future__ import annotations

import os
import shutil
import sys
from types import TracebackType
from typing import Any


class Terminal:
    """Responsabilidad: preparar la consola para un editor de pantalla completa
    (modo raw, pantalla alternativa, secuencias ANSI) y restaurarla al salir.

    Ítem de cambio que esconde: los detalles de cada sistema operativo para
    configurar la consola. Se usa como context manager para que la terminal
    quede bien aunque el programa termine con una excepción.
    """

    _ENTRAR = "\x1b[?1049h\x1b[H\x1b[2J"
    _SALIR = "\x1b[?1049l"

    def __init__(self) -> None:
        self._configuracion_previa: list[Any] | None = None

    def __enter__(self) -> Terminal:
        if sys.platform == "win32":
            os.system("")  # habilita las secuencias ANSI en la consola de Windows
        else:
            import termios
            import tty

            fd = sys.stdin.fileno()
            self._configuracion_previa = termios.tcgetattr(fd)
            tty.setraw(fd)
        self.escribir(self._ENTRAR)
        return self

    def __exit__(
        self,
        tipo: type[BaseException] | None,
        error: BaseException | None,
        traza: TracebackType | None,
    ) -> None:
        self.escribir("\x1b[0m" + self._SALIR)
        if sys.platform != "win32" and self._configuracion_previa is not None:
            import termios

            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self._configuracion_previa)

    def escribir(self, texto: str) -> None:
        sys.stdout.write(texto)
        sys.stdout.flush()

    def tamanio(self) -> tuple[int, int]:
        """(columnas, filas) de la terminal."""
        tam = shutil.get_terminal_size((80, 24))
        return tam.columns, tam.lines