"""Geracao do laudo de certificacao.

Certification report generation.
"""

from __future__ import annotations

from .classificador import APROVADO, Veredito, classificar
from .medicao import (
    LIMITES_ATENUACAO,
    LIMITES_NEXT,
    LIMITES_PS_NEXT,
    LIMITE_DESVIO_NS,
    LIMITE_RESISTENCIA_OHM,
    SEMENTE_FIXA,
    Perfil,
)
from .mapa import ErroDeMapa, T568B, conferir_mapa, detectar_split_pair


def _laudo_cabo(veredito: Veredito, nome_equipamento: str) -> list[str]:
    """Monta o laudo de um cabo.

    Build the report of one cable.
    """
    p = veredito.perfil
    m = veredito.medicao
    marca = "PASS" if veredito.aprovado else "FAIL"

    linhas = [
        f"## {p.nome}",
        "",
        "| Parametro | Valor | Limite | Situacao |",
        "|---|---|---|---|",
    ]
    for freq, medido in sorted(m["atenuacao"].items()):
        limite = LIMITES_ATENUACAO[p.categoria][freq]
        ok = medido <= limite
        linhas.append(
            f"| Atenuacao {freq} MHz | {medido:.2f} dB | <= {limite:.2f} dB | "
            f"{'ok' if ok else 'ESTOURA'} |"
        )
    for freq, medido in sorted(m["next"].items()):
        limite = LIMITES_NEXT[p.categoria][freq]
        ok = medido >= limite
        linhas.append(
            f"| NEXT {freq} MHz | {medido:.2f} dB | >= {limite:.2f} dB | "
            f"{'ok' if ok else 'ESTOURA'} |"
        )
    for freq, medido in sorted(m["ps_next"].items()):
        limite = LIMITES_PS_NEXT[p.categoria][freq]
        ok = medido >= limite
        linhas.append(
            f"| PS-NEXT {freq} MHz | {medido:.2f} dB | >= {limite:.2f} dB | "
            f"{'ok' if ok else 'ESTOURA'} |"
        )
    linhas.append(
        f"| Resistencia | {m['resistencia']:.2f} ohm | <= {LIMITE_RESISTENCIA_OHM:.1f} ohm | "
        f"{'ok' if m['resistencia'] <= LIMITE_RESISTENCIA_OHM else 'ESTOURA'} |"
    )
    linhas.append(
        f"| Desvio | {m['desvio']:.2f} ns | <= {LIMITE_DESVIO_NS:.1f} ns | "
        f"{'ok' if m['desvio'] <= LIMITE_DESVIO_NS else 'ESTOURA'} |"
    )
    linhas.append(f"| Comprimento | {p.comprimento_m:.2f} m | 90 m | "
                  f"{'ok' if p.comprimento_m <= 90 else 'ESTOURA'} |")
    linhas.append(f"| Categoria | {p.categoria} | - | - |")
    linhas.append("")

    if p.pinos:
        try:
            mapa = conferir_mapa(p.pinos, p.pinos)
            linhas.append(f"- Mapa pino a pino: {'conforme' if mapa.correto else 'NAO CONFORME'}")
            split = detectar_split_pair(p.pinos)
            linhas.append(f"- Split pair detectado: {'sim' if split else 'nao'}")
        except ErroDeMapa as exc:
            linhas.append(f"- Mapa pino a pino: nao conferido ({exc})")
        linhas.append("")

    if veredito.falhas:
        linhas.append("Itens estourados:")
        linhas.extend(f"- `{f}`" for f in veredito.falhas)
        linhas.append("")

    linhas.append(f"**{marca} - {veredito.situacao}**")
    linhas.append("")
    return linhas


def gerar_laudo(
    perfis: list[Perfil],
    nome_equipamento: str = "Certificador de cabo (simulado)",
    semente: int | None = None,
) -> str:
    """Gera o laudo de uma bateria de cabos.

    Generate the report for a batch of cables.

    Args:
        perfis: Os perfis a ensaiar.
        nome_equipamento: Nome no cabecalho.
        semente: Semente fixa da simulacao.

    Returns:
        O laudo em Markdown.
    """
    vereditos = [classificar(p, semente=semente) for p in perfis]
    aprovados = sum(1 for v in vereditos if v.aprovado)

    linhas = [
        "# Laudo de certificacao de cabos",
        "",
        "| Campo | Valor |",
        "|---|---|",
        f"| Equipamento | {nome_equipamento} |",
        f"| Cabos ensaiados | {len(perfis)} |",
        f"| Aprovados | {aprovados} |",
        f"| Reprovados | {len(perfis) - aprovados} |",
        f"| Semente | {SEMENTE_FIXA} (fixa, resultado deterministico) |",
        "",
        "> Simulacao estatistica com semente fixa. Nao e medicao real de "
        "equipamento e nao substitui certificacao em bancada.",
        "",
        "---",
        "",
    ]

    for v in vereditos:
        linhas.extend(_laudo_cabo(v, nome_equipamento))

    linhas += [
        "---",
        "",
        "## Resumo",
        "",
        "| Cabo | Categoria | Comprimento | Veredito |",
        "|---|---|---|---|",
    ]
    for v in vereditos:
        linhas.append(
            f"| {v.perfil.nome} | {v.perfil.categoria} | "
            f"{v.perfil.comprimento_m:.1f} m | {v.situacao} |"
        )

    return "\n".join(linhas)