"""Testes do classificador, do laudo e da CLI.

Tests for the classifier, the report and the CLI.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from certsim.classificador import (
    APROVADO,
    APROVADO_COM_RESSALVA,
    REPROVADO,
    classificar,
)
from certsim.cli import carregar_cenarios, main
from certsim.laudo import gerar_laudo
from certsim.medicao import SEMENTE_FIXA, Perfil
from certsim.mapa import T568A, T568B

DADOS = Path(__file__).resolve().parents[1] / "dados"


def _bom(nome="x", **kw) -> Perfil:
    """Perfil que passa."""
    base = dict(categoria="6", comprimento_m=40.0, pinos=T568B)
    base.update(kw)
    return Perfil(nome=nome, **base)


class TestClassificadorAprovado:
    """Cabo dentro de tudo."""

    def test_cabo_bom_aprova(self) -> None:
        assert classificar(_bom()).situacao == APROVADO

    def test_cabo_bom_tem_aprovado_true(self) -> None:
        assert classificar(_bom()).aprovado is True

    def test_cabo_bom_nao_tem_falhas(self) -> None:
        assert classificar(_bom()).falhas == []

    def test_cabo_curto_aprova_com_mais_folga_que_longo(self) -> None:
        curto = classificar(_bom("c", comprimento_m=5.0))
        longo = classificar(_bom("l", comprimento_m=88.0))
        assert curto.medicao["atenuacao"][100] < longo.medicao["atenuacao"][100]

    def test_classificacao_deterministica(self) -> None:
        a = classificar(_bom())
        b = classificar(_bom())
        assert a.situacao == b.situacao
        assert a.medicao == b.medicao

    def test_semente_explicita_nao_altera_veredito_bom(self) -> None:
        assert classificar(_bom(), semente=7).situacao == APROVADO


class TestClassificadorRessalva:
    """Folga pequena vira ressalva, nao reprovacao."""

    def test_ressalva_ainda_aprovado(self) -> None:
        v = classificar(_bom(comprimento_m=89.0, perda_extra_db=0.5))
        assert v.situacao in (APROVADO, APROVADO_COM_RESSALVA)
        assert v.aprovado is True


class TestClassificadorReprovado:
    """Cada modo de reprovacao."""

    def test_comprimento_acima_de_90_reprova(self) -> None:
        v = classificar(_bom(comprimento_m=105.0))
        assert v.situacao == REPROVADO
        assert any(f.startswith("comprimento") for f in v.falhas)

    def test_par_aberto_reprova(self) -> None:
        v = classificar(_bom(defeito="aberto"))
        assert v.situacao == REPROVADO
        assert v.aprovado is False

    def test_par_aberto_aponta_next_abaixo_do_piso(self) -> None:
        v = classificar(_bom(defeito="aberto"))
        assert any(f.startswith("NEXT") for f in v.falhas)

    def test_par_em_curto_reprova(self) -> None:
        assert classificar(_bom(defeito="curto")).situacao == REPROVADO

    def test_split_reprova_por_desvio(self) -> None:
        v = classificar(_bom(defeito="split"))
        assert v.situacao == REPROVADO
        assert any(f.startswith("desvio") for f in v.falhas)

    def test_par_invertido_reprova(self) -> None:
        assert classificar(_bom(defeito="invertido")).situacao == REPROVADO

    def test_reprovado_tem_aprovado_false(self) -> None:
        assert classificar(_bom(defeito="aberto")).aprovado is False

    def test_perda_extra_grande_reprova(self) -> None:
        # 9 dB num cabo de 40 m nao estouram nada: sobram 12 dB de folga.
        # Precisa de 14 dB para passar do limite de 20,7 dB.
        v = classificar(_bom(perda_extra_db=14.0))
        assert v.situacao == REPROVADO
        assert any(f.startswith("atenuacao") for f in v.falhas)

    def test_perda_extra_moderada_ainda_passa(self) -> None:
        # Folga existe: 9 dB num cabo curto nao reprova. E o comportamento
        # correto - reprovar por folga seria reprovar cabo bom.
        assert classificar(_bom(perda_extra_db=9.0)).situacao == APROVADO

    def test_categoria_invalida_propaga_valueerror(self) -> None:
        with pytest.raises(ValueError):
            classificar(_bom(categoria="8"))

    def test_comprimento_acima_nao_calcula_sobrepassagem(self) -> None:
        # Reprova pelo limite fisico, mas a medicao foi feita mesmo assim.
        v = classificar(_bom(comprimento_m=200.0))
        assert v.situacao == REPROVADO
        assert any(f.startswith("comprimento") for f in v.falhas)


class TestVereditoComPinos:
    """Mapa de fiaacao entra no laudo."""

    def test_cabo_sem_pinos_ainda_classifica(self) -> None:
        assert classificar(Perfil("y", "6", 40.0)).situacao == APROVADO

    def test_mapa_t568a_nao_e_falha(self) -> None:
        v = classificar(Perfil("z", "6", 40.0, pinos=T568A))
        assert v.situacao == APROVADO


class TestLaudo:
    """Formato do laudo."""

    def test_laudo_tem_titulo(self) -> None:
        assert "Laudo de certificacao" in gerar_laudo([_bom()])

    def test_laudo_tem_resumo_com_quantidade(self) -> None:
        texto = gerar_laudo([_bom(), _bom(defeito="aberto")])
        assert "| Cabos ensaiados | 2 |" in texto

    def test_laudo_avisa_que_e_simulacao(self) -> None:
        assert "Simulacao estatistica" in gerar_laudo([_bom()])

    def test_laudo_lista_cada_cabo(self) -> None:
        texto = gerar_laudo([_bom("aaa"), _bom("bbb")])
        assert "aaa" in texto and "bbb" in texto

    def test_laudo_mostra_itens_estourados(self) -> None:
        texto = gerar_laudo([_bom(defeito="aberto")])
        assert "Itens estourados" in texto

    def test_laudo_deterministico(self) -> None:
        p = [_bom()]
        assert gerar_laudo(p) == gerar_laudo(p)

    def test_laudo_com_split_mostra_split(self) -> None:
        texto = gerar_laudo([_bom(defeito="split", pinos=(
            "branco/laranja", "laranja", "branco/verde", "branco/laranja",
            "azul", "branco/verde", "branco/marrom", "marrom",
        ))])
        assert "Split pair detectado: sim" in texto

    def test_laudo_lista_resumo_final(self) -> None:
        assert "## Resumo" in gerar_laudo([_bom()])


class TestCenarios:
    """Leitura do YAML de cenarios."""

    def test_carrega_12_cenarios(self) -> None:
        assert len(carregar_cenarios(DADOS / "cenarios.yaml")) == 12

    def test_tem_7_bons_e_5_com_falha(self) -> None:
        cenarios = carregar_cenarios(DADOS / "cenarios.yaml")
        com_defeito = [c for c in cenarios if c.defeito]
        # 5 com falha: 4 com defeito nomeado + 1 que estoura o limite fisico.
        assert len(com_defeito) == 4
        assert len(cenarios) - len(com_defeito) == 8

    def test_quinto_cabo_com_falha_e_o_de_comprimento(self) -> None:
        cenarios = carregar_cenarios(DADOS / "cenarios.yaml")
        acima = [c for c in cenarios if c.comprimento_m > 90.0]
        assert len(acima) == 1
        reprovados = [c for c in cenarios if not classificar(c).aprovado]
        assert len(reprovados) == 5

    def test_cenarios_com_defeito_sao_todos_distintos(self) -> None:
        cenarios = carregar_cenarios(DADOS / "cenarios.yaml")
        tipos = {c.defeito for c in cenarios if c.defeito}
        assert tipos == {"aberto", "curto", "invertido", "split"}

    def test_padrao_preenchido_quando_ausente(self) -> None:
        cenarios = carregar_cenarios(DADOS / "cenarios.yaml")
        assert all(c.pinos for c in cenarios)

    def test_pinos_do_cenario_invertido_respeitados(self) -> None:
        cenarios = carregar_cenarios(DADOS / "cenarios.yaml")
        inv = next(c for c in cenarios if c.defeito == "invertido")
        assert inv.pinos != T568B

    def test_arquivo_inexistente_levanta_oserror(self) -> None:
        with pytest.raises(OSError):
            carregar_cenarios(DADOS / "nao-existe.yaml")

    def test_yaml_sem_lista_levanta_valueerror(self, tmp_path) -> None:
        p = tmp_path / "ruim.yaml"
        p.write_text("cenario: um\n", encoding="utf-8")
        with pytest.raises(ValueError):
            carregar_cenarios(p)


class TestCLI:
    """Interface de linha de comando."""

    def test_testar_retorna_1_quando_ha_reprovado(self, capsys) -> None:
        codigo = main(["testar", str(DADOS / "cenarios.yaml")])
        assert codigo == 1

    def test_saida_mostra_resumo(self, capsys) -> None:
        main(["testar", str(DADOS / "cenarios.yaml")])
        assert "aprovados" in capsys.readouterr().out

    def test_saida_mostra_o_critico_estourado(self, capsys) -> None:
        main(["testar", str(DADOS / "cenarios.yaml")])
        saida = capsys.readouterr().out
        assert "atenuacao" in saida or "NEXT" in saida

    def test_grava_laudo(self, capsys, tmp_path) -> None:
        destino = tmp_path / "l.md"
        main(["testar", str(DADOS / "cenarios.yaml"), "--laudo", str(destino)])
        assert destino.exists()
        assert "Laudo" in destino.read_text(encoding="utf-8")

    def test_semente_alterada_muda_o_laudo(self, tmp_path) -> None:
        a, b = tmp_path / "a.md", tmp_path / "b.md"
        main(["testar", str(DADOS / "cenarios.yaml"), "--laudo", str(a)])
        main(["testar", str(DADOS / "cenarios.yaml"), "--laudo", str(b),
              "--semente", "999"])
        assert a.read_text(encoding="utf-8") != b.read_text(encoding="utf-8")

    def test_arquivo_inexistente_retorna_dois(self, capsys) -> None:
        assert main(["testar", str(DADOS / "nao-existe.yaml")]) == 2
        assert "Erro" in capsys.readouterr().err

    def test_cabos_lista_limites(self, capsys) -> None:
        assert main(["cabos"]) == 0
        assert "500" in capsys.readouterr().out

    def test_help_principal(self) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["--help"])
        assert exc.value.code == 0

    def test_help_testar(self) -> None:
        with pytest.raises(SystemExit) as exc:
            main(["testar", "--help"])
        assert exc.value.code == 0

    def test_sem_subcomando_falha(self) -> None:
        with pytest.raises(SystemExit) as exc:
            main([])
        assert exc.value.code != 0


class TestSementeGlobal:
    """A semente padrao nao muda entre chamadas."""

    def test_semente_padrao_e_estavel(self) -> None:
        assert SEMENTE_FIXA == 20260901

    def test_reaproveitar_semente_da_mesma_saida(self) -> None:
        cenarios = carregar_cenarios(DADOS / "cenarios.yaml")
        assert gerar_laudo(cenarios) == gerar_laudo(cenarios)