<div align="center">

<img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python">
<img src="https://img.shields.io/badge/license-MIT-yellow?style=flat-square" alt="License">
<img src="https://img.shields.io/badge/deps-PyYAML%20only-blue?style=flat-square" alt="Dependencies">

</div>

# certificador-cobre-simulado

CLI that simulates network cable certification testing. It covers pin-by-pin wiring map, length, attenuation, NEXT, PS-NEXT, resistance, and propagation delay. It applies category and frequency limits and issues a report naming the parameter and frequency that exceed the limit.

## Problem / Why it exists

"Continuity passed" is the phrase that most delays a construction job. A cable with all eight wires connected can have pair 1 and pair 3 swapped, or a split pair that still passes continuity and fails NEXT. The technician tests the cable, the client complains, and someone has to come back to re-crimp.

The report only helps if it shows which side the limit is on. Attenuation is a ceiling; lower is better. NEXT is a floor; higher is better. Applying the wrong comparison sign on either one fails a good cable — the silent failure, of the kind that only shows up when the client calls.

## What it does

- Simulates cable certification testing: pin-by-pin map, length, attenuation, NEXT, PS-NEXT, resistance, and propagation delay.
- Applies limits by category (5e, 6, 6A) and frequency (100, 250, and 500 MHz).
- The verdict is APPROVED, APPROVED WITH RESERVATION (margin below 10% of the limit), or FAILED; it names parameter, frequency, measured value, and limit.
- It measures nothing real. Numbers come from a normal distribution with fixed seed (20260901), so the result is deterministic and reproducible.
- Generates a Markdown report with `--laudo`.

## Stack

- Python 3.10+
- PyYAML >= 6.0 (only runtime dependency)
- pytest >= 7.4 and pytest-cov >= 4.1 (development only)
- setuptools, source code in `src/`

## How it works

`dados/cenarios.yaml` defines 12 profiles. Seven are good cables and five have distinct faults — open pair, shorted pair, swapped pair, split pair, and length above 90 m.

The program runs in five steps:

1. `cli.py` reads the YAML and builds a `Perfil` per scenario.
2. `medicao.py` simulates the measurement with `random.Random(f"{semente}-{nome}")`, small noise (0.3 dB on attenuation, 0.4 dB on NEXT) and fixed seed.
3. `classificador.py` compares each parameter with the category limit. Attenuation, resistance, delay, and length are ceilings (<=); NEXT and PS-NEXT are floors (>=).
4. Length above 90 m fails before any calculation. A wiring fault fails even with good electrical numbers.
5. A margin below 10% of the limit becomes `APPROVED WITH RESERVATION`; the cable passes, but without margin for the environment.

Install the package and run the test suite.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -e .
python -m pytest tests/ -v
python -m certsim testar dados/cenarios.yaml
```

Actual output of the last command.

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

Each `->` line names the parameter, the frequency, the measured value, and the limit. The 5 failed cables do not fail due to loss. Two fail for wiring (open pair and shorted pair), one for swapped pair, one for split pair, and one for length above 90 m.

Other commands

```powershell
python -m certsim cabos                                     # limits by category
python -m certsim testar dados/cenarios.yaml --laudo exemplos/laudo-certificacao.md
python -m certsim testar dados/cenarios.yaml --semente 999   # another realization
```

## Project structure

```
certificador-cobre-simulado/
  src/certsim/
    __main__.py   entry point of `python -m certsim`
    cli.py        command-line interface (`testar`, `cabos`)
    classificador.py  verdict, exceeded limits, and reservation rule
    laudo.py      Markdown report output
    mapa.py       T568A/T568B, conferir_mapa, detectar_split_pair
    medicao.py    statistical simulation, fixed seed, limit tables
  dados/cenarios.yaml   12 scenarios (7 good, 5 with distinct faults)
  docs/                 o-que-e-certificacao.md, como-ler-um-laudo-de-cabo.md
  exemplos/             real execution and report outputs
  tests/                84 tests
  tools/                verificar_encoding.py
  pyproject.toml, requirements.txt, LICENSE
```

## Trade-offs and decisions

- Fixed seed instead of free noise gives a deterministic result, regression tests, and reproducible examples. The cost is that it is not real equipment measurement.
- Small noise by design. Large noise would hide exactly the defect the report must point out.
- `APPROVED WITH RESERVATION` instead of failing by margin. The first version failed everything within 10% of the limit due to a miswritten `any()` and failed a 90 m cable within the norm. Now small margin becomes reservation because the job needs to finish.
- Wiring map as a separate check. A split pair passes continuity and only shows up on NEXT; it is not a consequence of electrical measurement.
- Count per end, not both ends together. Joining the ends made every cable with identical ends look duplicated — the normal case.
- No English alias in the CLI. The same action never has two names.
- Human-readable report, not proprietary equipment format; not importable by third-party software.

## Known limitations

- It measures nothing. There is no sensor and no real sample. Every number comes from a normal distribution with fixed seed. It serves to apply the rules and teach how to read the report, not to replace a test bench.
- NEXT and PS-NEXT are synthetic. Coupling is simulated from the profile, not from pair geometry, which is what defines real ICR.
- It does not model temperature, bending, strapping, or splices. Small margin in a hot environment is a real case the tool does not see.
- It does not issue a report in any equipment manufacturer's proprietary format.
- The report has no acceptance value. A cable that fails here may pass on the manufacturer's equipment, and vice versa. For job decisions, measure.

## License

MIT. See [LICENSE](LICENSE).

## Author

Kelvin Oliveira — https://github.com/KelvinOliveiraCode — https://kelvinoliveiracode.github.io/portfolio/
