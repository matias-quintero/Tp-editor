"""Lectura de teclas en la consola (Windows y Linux/macOS)."""

from __future__ import annotations

import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto


class TipoTecla(Enum):
    CARACTER = auto()
    ENTER = auto()
    BORRAR_ATRAS = auto()
    BORRAR_ADELANTE = auto()
    IZQUIERDA = auto()
    DERECHA = auto()
    ARRIBA = auto()
    ABAJO = auto()
    INICIO = auto()
    FIN = auto()
    PAGINA_ARRIBA = auto()
    PAGINA_ABAJO = auto()
    DESHACER = auto()
    ALINEAR_IZQUIERDA = auto()
    ALINEAR_DERECHA = auto()
    ALINEAR_CENTRADO = auto()
    ALINEAR_JUSTIFICADO = auto()
    EXPORTAR = auto()
    SALIR = auto()
    DESCONOCIDA = auto()


@dataclass(frozen=True)
class Tecla:
    tipo: TipoTecla
    caracter: str = ""


_CONTROL: dict[str, TipoTecla] = {
    "\r": TipoTecla.ENTER,
    "\n": TipoTecla.ENTER,
    "\x08": TipoTecla.BORRAR_ATRAS,  # Backspace en Windows
    "\x7f": TipoTecla.BORRAR_ATRAS,  # Backspace en Linux/macOS
    "\x1a": TipoTecla.DESHACER,  # CTRL+Z
    "\x0c": TipoTecla.ALINEAR_IZQUIERDA,  # CTRL+L
    "\x12": TipoTecla.ALINEAR_DERECHA,  # CTRL+R
    "\x0e": TipoTecla.ALINEAR_CENTRADO,  # CTRL+E
    "\x14": TipoTecla.ALINEAR_JUSTIFICADO,  # CTRL+T
    "\x0f": TipoTecla.EXPORTAR,  # CTRL+O
    "\x13": TipoTecla.SALIR,  # CTRL+Q
    "\x03": TipoTecla.SALIR,  # CTRL+C
}

# Secuencias ANSI (lo que sigue al ESC) en terminales Unix
_ESCAPE: dict[str, TipoTecla] = {
    "[A": TipoTecla.ARRIBA,
    "[B": TipoTecla.ABAJO,
    "[C": TipoTecla.DERECHA,
    "[D": TipoTecla.IZQUIERDA,
    "OA": TipoTecla.ARRIBA,
    "OB": TipoTecla.ABAJO,
    "OC": TipoTecla.DERECHA,
    "OD": TipoTecla.IZQUIERDA,
    "[H": TipoTecla.INICIO,
    "[F": TipoTecla.FIN,
    "OH": TipoTecla.INICIO,
    "OF": TipoTecla.FIN,
    "[1~": TipoTecla.INICIO,
    "[7~": TipoTecla.INICIO,
    "[4~": TipoTecla.FIN,
    "[8~": TipoTecla.FIN,
    "[3~": TipoTecla.BORRAR_ADELANTE,
    "[5~": TipoTecla.PAGINA_ARRIBA,
    "[6~": TipoTecla.PAGINA_ABAJO,
}

# Segundo carácter de las teclas extendidas de msvcrt (Windows)
_EXTENDIDAS_WINDOWS: dict[str, TipoTecla] = {
    "H": TipoTecla.ARRIBA,
    "P": TipoTecla.ABAJO,
    "K": TipoTecla.IZQUIERDA,
    "M": TipoTecla.DERECHA,
    "G": TipoTecla.INICIO,
    "O": TipoTecla.FIN,
    "I": TipoTecla.PAGINA_ARRIBA,
    "Q": TipoTecla.PAGINA_ABAJO,
    "S": TipoTecla.BORRAR_ADELANTE,
}


def decodificar_caracter(caracter: str) -> Tecla:
    """Traduce un carácter simple (imprimible o de control) a una ``Tecla``."""
    if caracter in _CONTROL:
        return Tecla(_CONTROL[caracter])
    if caracter == "\t":
        return Tecla(TipoTecla.CARACTER, " ")
    if len(caracter) == 1 and caracter.isprintable():
        return Tecla(TipoTecla.CARACTER, caracter)
    return Tecla(TipoTecla.DESCONOCIDA)


def decodificar_escape(secuencia: str) -> Tecla:
    """Traduce lo que sigue a un ESC en una terminal ANSI."""
    return Tecla(_ESCAPE.get(secuencia, TipoTecla.DESCONOCIDA))


def decodificar_extendida_windows(codigo: str) -> Tecla:
    """Traduce el segundo carácter de una tecla extendida de Windows."""
    return Tecla(_EXTENDIDAS_WINDOWS.get(codigo, TipoTecla.DESCONOCIDA))


class LectorTeclas(ABC):
    """Responsabilidad: leer una tecla de la consola y devolverla ya traducida.

    Ítem de cambio que esconde: las diferencias entre sistemas operativos
    (msvcrt en Windows, secuencias ANSI en modo raw en Unix). El controlador
    solo ve ``Tecla``.
    """

    @abstractmethod
    def leer(self) -> Tecla: ...


if sys.platform == "win32":
    import msvcrt

    class LectorTeclasWindows(LectorTeclas):
        def leer(self) -> Tecla:
            caracter = msvcrt.getwch()
            if caracter in ("\x00", "\xe0"):
                return decodificar_extendida_windows(msvcrt.getwch())
            return decodificar_caracter(caracter)

    def crear_lector() -> LectorTeclas:
        return LectorTeclasWindows()

else:
    import codecs
    import select

    class LectorTeclasUnix(LectorTeclas):
        """Requiere que la terminal esté en modo raw (ver ``Terminal``)."""

        def __init__(self, descriptor: int) -> None:
            self._fd = descriptor
            self._decodificador = codecs.getincrementaldecoder("utf-8")(errors="replace")

        def leer(self) -> Tecla:
            caracter = self._leer_caracter()
            if caracter == "\x1b":
                return decodificar_escape(self._leer_secuencia())
            return decodificar_caracter(caracter)

        def _leer_caracter(self) -> str:
            while True:
                byte = os.read(self._fd, 1)
                if not byte:
                    return "\x13"  # entrada cerrada: salir
                caracter = self._decodificador.decode(byte)
                if caracter:
                    return caracter

        def _hay_datos(self) -> bool:
            listos, _, _ = select.select([self._fd], [], [], 0.05)
            return bool(listos)

        def _leer_secuencia(self) -> str:
            if not self._hay_datos():
                return ""  # ESC suelto
            secuencia = os.read(self._fd, 1).decode("latin-1")
            if secuencia not in ("[", "O"):
                return secuencia
            while len(secuencia) < 8 and self._hay_datos():
                caracter = os.read(self._fd, 1).decode("latin-1")
                secuencia += caracter
                if caracter.isalpha() or caracter == "~":
                    break
            return secuencia

    def crear_lector() -> LectorTeclas:
        return LectorTeclasUnix(sys.stdin.fileno())