"""Punto de entrada del editor.

Uso (desde la carpeta ``editor/``):

    python -m src.main [archivo.txt] [--ancho 60] [--lineas 20] [--exportar-a salida.txt]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.alineacion.alineadores import AlineadorIzquierda
from src.comandos.historial import HistorialComandos
from src.edicion.editor import Editor
from src.layout.maquetador import Maquetador
from src.vista.controlador import ControladorConsola
from src.vista.pantalla import Pantalla
from src.vista.teclado import crear_lector
from src.vista.terminal import Terminal


def normalizar(texto: str) -> str:
    """Deja el texto con '\\n' como único separador y sin caracteres de control."""
    texto = texto.replace("\r\n", "\n").replace("\r", "\n").replace("\t", " ")
    return "".join(c for c in texto if c == "\n" or c.isprintable())


def _argumentos(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Editor de texto por consola")
    parser.add_argument("archivo", nargs="?", help="archivo de texto para abrir (opcional)")
    parser.add_argument("--ancho", type=int, default=60, help="caracteres por línea")
    parser.add_argument("--lineas", type=int, default=20, help="líneas por página")
    parser.add_argument(
        "--exportar-a", default="documento_exportado.txt", help="destino de CTRL+O"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _argumentos(argv)
    if args.ancho < 10 or args.lineas < 1:
        print("El ancho debe ser >= 10 y las líneas por página >= 1", file=sys.stderr)
        return 2
    if not sys.stdin.isatty():
        print("El editor necesita una terminal interactiva.", file=sys.stderr)
        return 1

    texto = ""
    if args.archivo:
        ruta = Path(args.archivo)
        try:
            texto = normalizar(ruta.read_text(encoding="utf-8"))
        except OSError as error:
            print(f"No se pudo abrir {ruta}: {error}", file=sys.stderr)
            return 1

    maquetador = Maquetador(args.ancho, args.lineas, AlineadorIzquierda())
    editor = Editor(maquetador, texto)
    with Terminal() as terminal:
        controlador = ControladorConsola(
            editor=editor,
            historial=HistorialComandos(),
            pantalla=Pantalla(terminal.escribir),
            lector=crear_lector(),
            ruta_exportacion=Path(args.exportar_a),
        )
        controlador.ejecutar(terminal)
    return 0


if __name__ == "__main__":
    sys.exit(main())