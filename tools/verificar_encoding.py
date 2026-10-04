"""Confere o encoding dos arquivos de texto do repositorio.

Check the encoding of every text file in the repository.

Um BOM UTF-8 no inicio, um caractere de substituicao (U+FFFD) ou um
ideograma CJK dentro de um arquivo versionado indicam que alguma
passagem de texto corrompeu a escrita. No GitHub o resultado aparece
como lixo no diff, entao e mais barato falhar aqui.

Um BOM e o marcador de byte de ordem no comeco do arquivo. Um U+FFFD
e um caractere de substituicao. Um ideograma CJK e um caractere em
japones, chines ou coreano. Nenhum dos tres pertence a este
repositorio.
"""

from __future__ import annotations

import sys
from pathlib import Path

#: Raiz do repositorio.
RAIZ = Path(__file__).resolve().parent.parent

#: Extensoes varridas. Binarios ficam de fora de proposito.
EXTENSOES = {
    ".py", ".md", ".txt", ".json", ".yml", ".yaml", ".toml", ".cfg",
    ".ini", ".ps1",
}

#: Nomes de diretorios ou arquivos ignorados em qualquer nivel.
IGNORADOS = {
    ".git", "__pycache__", ".pytest_cache", ".coverage",
}

#: BOM UTF-8: os tres bytes de ordem no inicio do arquivo.
BOM_UTF8 = b"\xef\xbb\xbf"

#: Ponto de codigo do caractere de substituicao.
SUBSTITUICAO = 0xFFFD

#: Faixas de codigo de ideogramas e silabas CJK.
CJK_RANGOS = (
    (0x3000, 0x9FFF),
    (0x1100, 0x11FF),
    (0x3130, 0x318F),
    (0xAC00, 0xD7AF),
    (0xF900, 0xFAFF),
    (0x20000, 0x2EBEF),
)


def eh_cjk(ponto: int) -> bool:
    """Diz se um ponto de codigo cai em uma faixa CJK.

    Say whether a code point falls inside a CJK range.
    """
    return any(inicio <= ponto <= fim for inicio, fim in CJK_RANGOS)


def varrer(raiz: Path = RAIZ) -> tuple[list[tuple[str, int, str]], int]:
    """Procura arquivo de texto com encoding invalido.

    Find text files holding an invalid encoding.

    Confere BOM UTF-8 no inicio, caractere de substituicao U+FFFD e
    ideograma CJK em cada arquivo de texto da raiz.

    Args:
        raiz: Diretorio a varrer.

    Returns:
        Tupla ``(problemas, conferidos)``. Cada problema e um
        ``(caminho, linha, motivo)``.
    """
    problemas: list[tuple[str, int, str]] = []
    conferidos = 0
    for caminho in sorted(raiz.rglob("*")):
        if not caminho.is_file():
            continue
        if any(parte in IGNORADOS for parte in caminho.parts):
            continue
        if caminho.suffix.lower() not in EXTENSOES:
            continue
        conferidos += 1
        bruto = caminho.read_bytes()
        relativo = str(caminho.relative_to(raiz))
        if bruto.startswith(BOM_UTF8):
            problemas.append((
                relativo, 0, "BOM UTF-8 no inicio do arquivo",
            ))
            continue
        try:
            texto = bruto.decode("utf-8")
        except UnicodeDecodeError as exc:
            problemas.append((
                relativo, 0, f"nao decodifica como UTF-8: {exc}",
            ))
            continue
        for numero, linha in enumerate(texto.splitlines(), 1):
            for caractere in linha:
                ponto = ord(caractere)
                if ponto == SUBSTITUICAO:
                    problemas.append((
                        relativo, numero,
                        "caractere de substituicao U+FFFD",
                    ))
                    break
                if eh_cjk(ponto):
                    problemas.append((
                        relativo, numero,
                        f"ideograma CJK U+{ponto:04X}",
                    ))
                    break
    return problemas, conferidos


def main() -> int:
    """Executa a varredura e reporta.

    Run the sweep and report.
    """
    problemas, conferidos = varrer()
    if not problemas:
        print(f"encoding ok: {conferidos} arquivos conferidos, "
              "nenhum BOM, nenhum U+FFFD e nenhum ideograma CJK")
        return 0
    print(f"encoding FALHOU: {len(problemas)} problema(s) "
          f"em {conferidos} arquivos conferidos")
    for caminho, linha, motivo in problemas:
        onde = f"{caminho}:{linha}" if linha else caminho
        print(f"  {onde}: {motivo}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
