<div align="center">

<img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
<img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="License">
<img src="https://img.shields.io/badge/deps-PyYAML%20apenas-blue?style=flat-square" alt="Dependencias">

</div>

# certificador-cobre-simulado

CLI que simula o ensaio de certificacao de cabo de rede: mapa de fiação pino a pino, comprimento, atenuação, NEXT, PS-NEXT, resistência e desvio de propagação. Aplica os limites por categoria e frequência e emite laudo com o parâmetro e a frequência que estouram.

## Problema / Por que existe

"Continuidade passou" é a frase que mais atrasa uma obra. Um cabo com os oito fios ligados pode ter o par 1 e o par 3 invertidos, ou um split pair que continua passando em continuidade e reprovando em NEXT. O técnico passa o cabo, o cliente reclama, e alguém volta para recrimpar.

O laudo só ajuda se mostra para que lado está o limite. Atenuação é teto: menor é melhor. NEXT é piso: maior é melhor. Aplicar o sinal de comparação errado nos dois reprova cabo bom — a falha silenciosa, do tipo que só aparece quando o cliente liga.

## O que faz

- Simula ensaio de certificação de cabo: mapa pino a pino, comprimento, atenuação, NEXT, PS-NEXT, resistência e desvio de propagação.
- Aplica os limites por categoria (5e, 6, 6A) e frequência (100, 250 e 500 MHz).
- Devolve veredito: APROVADO, APROVADO COM RESSALVA (folga menor que 10% do limite) ou REPROVADO, nomeando parâmetro, frequência, valor medido e limite.
- Mede nada de verdade: os números saem de uma distribuição normal com semente fixa (20260901), então o resultado é determinístico e reproduzível.
- Gera laudo em Markdown com `--laudo`.

## Stack

- Python 3.10+
- PyYAML >= 6.0 (única dependência de runtime)
- pytest >= 7.4 e pytest-cov >= 4.1 (apenas desenvolvimento)
- setuptools, código-fonte em `src/`

## Como funciona

`dados/cenarios.yaml` define 12 perfis: 7 cabos bons e 5 com falhas distintas — par aberto, par em curto, par invertido, split pair e comprimento acima de 90 m.

O fluxo é:

1. `cli.py` lê o YAML e constrói um `Perfil` por cenário.
2. `medicao.py` simula a medição com `random.Random(f"{semente}-{nome}")`, ruído pequeno (0,3 dB na atenuação, 0,4 dB no NEXT) e semente fixa.
3. `classificador.py` compara cada parâmetro com o limite da categoria. Atenuação, resistência, desvio e comprimento são teto (<=); NEXT e PS-NEXT são piso (>=).
4. Comprimento acima de 90 m reprova antes de qualquer conta. Defeito de fiação reprova mesmo com números elétricos bons.
5. Folga menor que 10% do limite vira `APROVADO COM RESSALVA`: o cabo passa, mas sem margem para ambiente.

Comandos:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
python -m pytest tests/ -v
python -m certsim testar dados/cenarios.yaml
```

Saída real do último comando:

```
CABO                   CAT     COMP  SITUACAO
--------------------- ---- -------  ----------------------
cabo-01-cat6-ok        6      45.0m  APROVADO
cabo-02-cat6-ok-longo  6      88.0m  APROVADO
cabo-03-cat6a-ok       6A     90.0m  APROVADO COM RESSALVA
cabo-04-cat6a-curto    6A     12.0m  APROVADO
cabo-05-cat6-padrao-a  6      60.0m  APROVADO
cabo-06-cat6-ressalva  6      84.0m  APROVADO
cabo-07-cat6a-maximo   6A     89.5m  APROVADO COM RESSALVA
cabo-08-par-aberto     6      50.0m  REPROVADO
                                     -> NEXT/100/30.58 dB/41.80 dB
                                     -> NEXT/250/28.97 dB/38.60 dB
                                     -> resistencia/--/81.00 ohm/24.0 ohm
                                     -> fiação/aberto/--/--
cabo-09-par-em-curto   6      50.0m  REPROVADO
                                     -> fiação/curto/--/--
cabo-10-par-invertido  6      40.0m  REPROVADO
                                     -> fiação/invertido/--/--
cabo-11-split-pair     6      55.0m  REPROVADO
                                     -> desvio/--/13.29 ns/5.0 ns
                                     -> fiação/split/--/--
cabo-12-comprimento-acima 6     105.0m  REPROVADO
                                     -> comprimento/--/105.00 m/90 m

7/12 aprovados
```

Cada linha `->` nomeia o parâmetro, a frequência, o valor medido e o limite. Os 5 reprovados não falham por perda: dois por fiação (par aberto e par em curto), um por par invertido, um por split pair e um por comprimento acima de 90 m.

Outros comandos:

```powershell
python -m certsim cabos                                     # limites por categoria
python -m certsim testar dados/cenarios.yaml --laudo exemplos/laudo-certificacao.md
python -m certsim testar dados/cenarios.yaml --semente 999   # outra realização
```

## Estrutura do projeto

```
certificador-cobre-simulado/
  src/certsim/
    __main__.py   ponto de entrada de `python -m certsim`
    cli.py        interface de linha de comando (`testar`, `cabos`)
    classificador.py  veredito, limites estourados e regra de ressalva
    laudo.py      saida em Markdown do laudo
    mapa.py       T568A/T568B, conferir_mapa, detectar_split_pair
    medicao.py    simulacao estatistica, semente fixa, tabelas de limite
  dados/cenarios.yaml   12 cenarios (7 bons, 5 com falhas distintas)
  docs/                 o-que-e-certificacao.md, como-ler-um-laudo-de-cabo.md
  exemplos/             saidas reais de execucao e de laudo
  tests/                84 testes
  tools/                verificar_encoding.py
  pyproject.toml, requirements.txt, LICENSE
```

## Trade-offs e decisões

- Semente fixa em vez de ruído livre: resultado determinístico, teste de regressão e exemplos reproduzíveis. Custo: não é medição de equipamento real.
- Ruído pequeno propositalmente: ruído grande esconderia exatamente o defeito que o laudo deve apontar.
- `APROVADO COM RESSALVA` em vez de reprovar por folga: a primeira versão reprovava tudo dentro de 10% do limite por um `any()` mal escrito e reprovava cabo de 90 m dentro da norma. Agora a folga pequena vira ressalva porque a obra precisa terminar.
- Mapa de fiação como checagem separada: split pair passa na continuidade e só aparece no NEXT; não é consequência da medição elétrica.
- Contar por ponta, não pelas duas juntas: juntar as pontas fazia todo cabo com pontas iguais parecer duplicado — o caso normal.
- Sem apelido em inglês na CLI: a mesma ação nunca tem dois nomes.
- Laudo legível por pessoa, não formato proprietário de equipamento; não é importável por software de terceiros.

## Limitações conhecidas

- Não mede nada: não há sensor nem amostra real. Todo número sai de uma distribuição normal com semente fixa. Serve para aplicar as regras e ensinar a ler o laudo, não para substituir bancada.
- NEXT e PS-NEXT são sintéticos: o acoplamento é simulado a partir do perfil, não da geometria do par, que é o que define o ICR de verdade.
- Não modela temperatura, curvatura, grampeamento nem emenda. Folga pequena em ambiente quente é um caso real que a ferramenta não enxerga.
- Não emite laudo no formato proprietário de nenhum equipamento.
- O laudo não tem valor de aceite: um cabo que reprova aqui pode passar no equipamento do fabricante, e o inverso também vale. Para decisão de obra, meça.

## Licença

MIT. Veja [LICENSE](LICENSE).

## Autor

Kelvin Oliveira — https://github.com/KelvinOliveiraCode — https://kelvinoliveiracode.github.io/portfolio/
