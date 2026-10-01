"""CLI do certsim.

CLI entry point for certsim.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

from .classificador import classificar
from .laudo import gerar_laudo
from .medicao import SEMENTE_FIXA, Perfil
from .mapa import T568A, T568B

PADROES = {"T568B": T568B, "T568A": T568A}


def carregar_cenarios(caminho: str | Path) -> list[Perfil]:
    """Le os cenarios de um YAML.

    Read the scenarios from a YAML file.

    Args:
        caminho: Caminho do ``.yaml``.

    Returns:
        A lista de :class:`Perfil`.
    """
    with open(caminho, "r", encoding="utf-8") as fh:
        dados = yaml.safe_load(fh)

    if isinstance(dados, dict):
        dados = dados.get("cenarios")
    if not isinstance(dados, list):
        raise ValueError(
            "Esperado uma lista de cenarios, ou um mapa com a chave 'cenarios' "
            "/ expected a list of scenarios, or a map with the 'cenarios' key"
        )

    perfis: list[Perfil] = []
    for item in dados:
        pinos = item.get("pinos") or list(PADROES.get(item.get("padrao", "T568B"), T568B))
        perfis.append(
            Perfil(
                nome=str(item["nome"]),
                categoria=str(item.get("categoria", "6")),
                comprimento_m=float(item.get("comprimento_m", 90.0)),
                perda_extra_db=float(item.get("perda_extra_db", 0.0)),
                crosstalk_db=float(item.get("crosstalk_db", 55.0)),
                resistencia_ohm=float(item.get("resistencia_ohm", 21.0)),
                desvio_ps_ns=float(item.get("desvio_ps_ns", 4.0)),
                defeito=item.get("defeito"),
                pinos=tuple(pinos),
            )
        )
    return perfis


def _cmd_testar(args: argparse.Namespace) -> int:
    """Executa a bateria de certificacao.

    Run the certification batch.
    """
    perfis = carregar_cenarios(args.cenarios)
    vereditos = [classificar(p, semente=args.semente) for p in perfis]

    print(f"{'CABO':<22} {'CAT':<4} {'COMP':>7}  SITUACAO")
    print(f"{'-' * 22} {'-' * 4} {'-' * 7}  {'-' * 22}")
    for v in vereditos:
        print(
            f"{v.perfil.nome:<22} {v.perfil.categoria:<4} "
            f"{v.perfil.comprimento_m:>6.1f}m  {v.situacao}"
        )
        for f in v.falhas:
            print(f"{'':<36}-> {f}")

    reprovados = [v for v in vereditos if not v.aprovado]
    print()
    print(f"{len(vereditos) - len(reprovados)}/{len(vereditos)} aprovados")

    if args.laudo:
        destino = Path(args.laudo)
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(
            gerar_laudo(perfis, semente=args.semente), encoding="utf-8"
        )
        print(f"Laudo gravado em: {destino}")

    return 1 if reprovados else 0


def _cmd_cabos(args: argparse.Namespace) -> int:
    """Mostra os limites por categoria.

    Show the limits per category.
    """
    from .medicao import LIMITES_ATENUACAO, LIMITES_NEXT

    for cat in sorted(LIMITES_ATENUACAO):
        freqs = sorted(LIMITES_ATENUACAO[cat])
        print(f"Categoria {cat}:")
        for f in freqs:
            print(
                f"  {f:>4} MHz   atenuacao <= {LIMITES_ATENUACAO[cat][f]:>5.2f} dB"
                f"   NEXT >= {LIMITES_NEXT[cat][f]:>5.2f} dB"
            )
    return 0


def construir_parser() -> argparse.ArgumentParser:
    """Monta o parser de argumentos.

    Build the argument parser.
    """
    parser = argparse.ArgumentParser(
        prog="certsim",
        description=(
            "Simula teste de certificacao de cabo de rede e emite laudo. "
            "Simulates network cable certification and emits a report."
        ),
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    p_test = sub.add_parser("testar", help="Ensaia uma bateria de cabos.")
    p_test.add_argument("cenarios", help="YAML com os cenarios.")
    p_test.add_argument("--laudo", help="Grava o laudo Markdown neste caminho.")
    p_test.add_argument(
        "--semente", type=int, default=SEMENTE_FIXA, help="Semente da simulacao."
    )
    p_test.set_defaults(func=_cmd_testar)

    p_cab = sub.add_parser("cabos", help="Mostra limites por categoria.")
    p_cab.set_defaults(func=_cmd_cabos)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada da CLI.

    CLI entry point.
    """
    parser = construir_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except (OSError, ValueError, KeyError) as exc:
        print(f"Erro / error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())