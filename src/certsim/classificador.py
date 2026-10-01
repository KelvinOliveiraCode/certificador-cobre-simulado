"""Veredito de certificacao a partir da medicao simulada.

Certification verdict from a simulated measurement.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .medicao import (
    LIMITE_CANAL_M,
    LIMITE_DESVIO_NS,
    LIMITES_ATENUACAO,
    LIMITES_NEXT,
    LIMITES_PS_NEXT,
    LIMITE_RESISTENCIA_OHM,
    Perfil,
    medir,
)

APROVADO = "APROVADO"
APROVADO_COM_RESSALVA = "APROVADO COM RESSALVA"
REPROVADO = "REPROVADO"


@dataclass
class Veredito:
    """Veredito de certificacao de um cabo.

    Certification verdict of a cable.

    Atributos:
        situacao: Uma das tres situacoes.
        falhas: Lista de linhas ``parametro/freq/medido/limite``.
        perfil: O perfil avaliado.
        medicao: Os numeros medidos.
    """

    situacao: str = APROVADO
    falhas: list[str] = field(default_factory=list)
    perfil: Perfil = field(default_factory=lambda: Perfil("desconhecido"))
    medicao: dict = field(default_factory=dict)

    @property
    def aprovado(self) -> bool:
        """Se o cabo serve.

        Whether the cable is usable.
        """
        return self.situacao in (APROVADO, APROVADO_COM_RESSALVA)


def classificar(perfil: Perfil, semente: int | None = None) -> Veredito:
    """Classifica um cabo medido.

    Classify a measured cable.

    A regra de ressalva vale para todos os parametros com limite: se a folga
    fica menor que 10% do limite, o cabo passa com ressalva em vez de reprovar.
    Sem essa faixa, um cabo a 0,05 dB do limite reprova - e 0,05 dB esta dentro
    da dispersao de qualquer equipamento real.

    Args:
        perfil: O perfil do cabo.
        semente: Semente fixa. ``None`` usa a semente global.

    Returns:
        Um :class:`Veredito`.
    """
    from .medicao import SEMENTE_FIXA

    medicao = medir(perfil, semente=SEMENTE_FIXA if semente is None else semente)
    veredito = Veredito(perfil=perfil, medicao=medicao)

    # Comprimento acima do limite fisico reprova antes de qualquer conta.
    if perfil.comprimento_m > LIMITE_CANAL_M:
        veredito.situacao = REPROVADO
        veredito.falhas.append(
            f"comprimento/{'--'}/{perfil.comprimento_m:.2f} m/{LIMITE_CANAL_M:.0f} m"
        )
        return veredito

    limite_peio = False
    cat = perfil.categoria

    for freq, medido in medicao["atenuacao"].items():
        limite = LIMITES_ATENUACAO[cat][freq]
        if medido > limite:
            veredito.falhas.append(f"atenuacao/{freq}/{medido:.2f} dB/{limite:.2f} dB")
            limite_peio = True
        elif medido > limite * 0.90:
            limite_peio = True

    for freq, medido in medicao["next"].items():
        limite = LIMITES_NEXT[cat][freq]
        if medido < limite:
            veredito.falhas.append(f"NEXT/{freq}/{medido:.2f} dB/{limite:.2f} dB")
            limite_peio = True

    for freq, medido in medicao["ps_next"].items():
        limite = LIMITES_PS_NEXT[cat][freq]
        if medido < limite:
            veredito.falhas.append(f"PS-NEXT/{freq}/{medido:.2f} dB/{limite:.2f} dB")
            limite_peio = True

    if medicao["resistencia"] > LIMITE_RESISTENCIA_OHM:
        veredito.falhas.append(
            f"resistencia/--/{medicao['resistencia']:.2f} ohm/"
            f"{LIMITE_RESISTENCIA_OHM:.1f} ohm"
        )
        limite_peio = True

    if medicao["desvio"] > LIMITE_DESVIO_NS:
        veredito.falhas.append(
            f"desvio/--/{medicao['desvio']:.2f} ns/{LIMITE_DESVIO_NS:.1f} ns"
        )
        limite_peio = True

    # Defeito de fiaacao pesado: reprova mesmo com numeros bons.
    if perfil.defeito in ("aberto", "curto", "invertido", "split"):
        veredito.falhas.append(f"fiacao/{perfil.defeito}/--/--")

    reprovou_valor = any(
        not f.startswith("fiac ao") for f in veredito.falhas
    )
    if veredito.falhas and reprovou_valor:
        veredito.situacao = REPROVADO
    elif veredito.falhas or limite_peio:
        veredito.situacao = APROVADO_COM_RESSALVA
    else:
        veredito.situacao = APROVADO

    return veredito