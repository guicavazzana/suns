# suns

Biblioteca para corrigir o espectro de um SUNS (espectrômetro/telescópio de
calibração solar) das perdas ópticas de cada elemento no caminho do feixe —
divisores de feixe, filtros de densidade neutra, revestimentos de lente,
placas dicroicas, fibra — cujas curvas de transmitância/refletância foram
digitalizadas de gráficos de datasheet (ex.: com PlotDigitizer).

```bash
pip install suns
```

```python
from suns import OpticalElement, apply_correction, read_suns_raw
```

Código-fonte: https://github.com/guicavazzana/suns · Pacote: https://pypi.org/project/suns/

---

## Início rápido

O fluxo é sempre o mesmo, em quatro passos:

```python
from pathlib import Path
from suns import OpticalElement, apply_correction, generate_report, read_suns_raw

# 1. importar (acima)

# 2. apontar para os dados brutos do SUNS — uma pasta com um .txt por
#    varredura do espectrômetro (seção "Begin Spectral Data")
suns = read_suns_raw("SUNS_pre-firstlight")
wl, dn = suns["wavelength"].values, suns["dn"].values

# os elementos ópticos do caminho do feixe
DADOS = Path("dados")
elementos = [
    OpticalElement(name="Divisor PDOT-2", path=DADOS / "divisor.csv", kind="direct"),
    OpticalElement(name="Filtro OD 1.0",  path=DADOS / "filtro_1_0.csv", kind="direct"),
    OpticalElement(name="Dubleto acromático", path=DADOS / "dubleto.csv", kind="reflection_loss"),
]

# 3. escolher o que aplicar — só um/alguns filtros:
_, corrigido_parcial = apply_correction(wl, dn, elementos[:2])
# ...ou a calibração total (todos os elementos, com todas as figuras):
resultado, corrigido_total = generate_report(wl, dn, elementos, out_dir="resultados")

# 4. ver a curva de cada item óptico
for el in elementos:
    el.plot_curve(f"curvas/{el.slug()}.png")
```

Se você já tem um CSV com o espectro médio pronto (colunas `wavelength`,
`dn`) em vez das varreduras brutas, use `read_suns_spectrum(caminho)` no
lugar de `read_suns_raw`.

---

## Conceitos

### `OpticalElement` — um elemento óptico no caminho do feixe

```python
elemento = OpticalElement(
    name="ND filter OD 1.0",       # nome (aparece em títulos, legendas e nomes de arquivo)
    path="dados/filtro_od10.csv",  # CSV digitalizado (qualquer um dos dois formatos, ver abaixo)
    kind="direct",                 # "direct" ou "reflection_loss" (ver abaixo)
    percent=True,                  # valores digitalizados estão em escala 0-100 (padrão) ou já 0-1
    enabled=True,                  # False = mantém o elemento na lista mas exclui ele da conta
)
```

**`kind`** diz o que o valor digitalizado *significa* para a luz que chega
no SUNS:

- **`"direct"`**: o valor já É a fração de luz que chega ao SUNS através
  desse elemento (transmissão de um filtro, de uma fibra, ou a refletância
  do lado *de trabalho* de um divisor de feixe — quando é o lado refletido
  que segue para o SUNS).
- **`"reflection_loss"`**: o valor é uma refletância que *tira* luz do
  caminho de transmissão desejado (ex.: refletância residual do
  revestimento AR de uma lente); a transmitância é `1 - valor`.

**`enabled`** (padrão `True`) desliga um elemento sem apagar a linha — ver
"Guia do usuário" abaixo.

```python
T = elemento.transmittance(wl_grid)   # np.ndarray, mesma forma de wl_grid
elemento.data()                       # DataFrame(wavelength, value) — a curva crua digitalizada
elemento.plot_curve("saida.png")      # plota só a curva desse elemento
```

`transmittance` avisa (`UserWarning`, não erro) se o `wl_grid` pedido for
mais largo que o range digitalizado (extrapola constante nas pontas), e
avisa de novo se der T fora de `[0, 1]` antes de recortar (`clip=True` por
padrão) — os dois avisos costumam apontar um `kind` ou CSV errado.

### Os dois formatos de CSV que `read_digitized_csv` aceita

Não precisa saber de antemão qual dos dois um arquivo usa — o leitor trata
qualquer linha cujos dois primeiros tokens (separados por vírgula) sejam
ambos conversíveis pra float como uma linha de dado `(wavelength, value)`;
todo o resto é ignorado silenciosamente.

```
# "limpo" — primeira linha já é o cabeçalho real
WAVELENGTH (nm),PERCENT
201.591,37.9487

# "bruto" — exportação nativa do PlotDigitizer
"Relative Transmission(Wavelength (nm)), created by Plot Digitizer, 2.6.12"
"Date: 13/09/2026, 15:32:33"

179
Wavelength (nm),Relative Transmission
198.071,81.4550,
```

### Dados do SUNS: um arquivo, uma pasta, uma lista de arquivos, ou já processado

```python
espectro = read_suns_raw("SUNS_firstlight_HR4D31871__0__13-51-47.txt")   # UM .txt bruto — sem média
espectro = read_suns_raw("SUNS_pre-firstlight")                          # pasta inteira de .txt -> média
espectro = read_suns_raw(["scan_a.txt", "scan_b.txt", "scan_c.txt"])     # só esses, escolhidos à mão -> média
espectro = read_suns_spectrum("espectro_medio.csv")                      # ou um CSV (wavelength, dn) já processado
```

`read_suns_raw` aceita:

- **um único arquivo** — o `.txt` que você acabou de tirar de uma
  observação, lido direto, sem precisar de mais nada;
- **uma pasta** com vários (cada um com uma seção `Begin Spectral Data`) —
  lê todos que baterem com `pattern` (padrão `"*.txt"`) e faz a média por
  comprimento de onda entre eles;
- **uma lista/tupla de caminhos** — pra quando você quer a média de um
  subconjunto escolhido à mão (não *todo mundo* de uma pasta), ou de
  arquivos espalhados em pastas diferentes.

### `apply_correction` e `generate_report` — escolher o que aplicar

```python
# um ou mais filtros, isolados:
resultado, corrigido = apply_correction(wl, dn, [filtro_od10])
resultado, corrigido = apply_correction(wl, dn, [filtro_od10, filtro_od13])

# a calibração total (todos os elementos do caminho):
resultado, corrigido = apply_correction(wl, dn, elementos)
```

É a mesma função para as duas coisas — a única diferença é quais elementos
você passa na lista. `generate_report` faz a mesma conta e além disso
escreve todas as figuras em disco (ver "Saída" abaixo).

### `write_corrected_csv` — salvar o resultado numérico, não só o gráfico

```python
from suns import write_corrected_csv

resultado, corrigido = apply_correction(wl, dn, [pdot, filtro_od10])
write_corrected_csv(wl, corrigido, "espectro_corrigido_pdot_filtro10.csv")
```

Grava um CSV com colunas `wavelength`, `dn` — o mesmo formato que
`read_suns_spectrum` lê de volta. Chame de novo pra cada combinação de
elementos que quiser guardar (um filtro, vários, todos).

---

## Guia do usuário: adicionar, remover, trocar e ajustar

Tudo é uma **lista Python comum** de `OpticalElement` — não existe
configuração em outro lugar. A lista *é* a configuração.

**Adicionar um elemento novo** — CSV digitalizado + uma entrada na lista:

```python
elementos.append(
    OpticalElement(name="Espelho X", path=DADOS / "espelho_x.csv", kind="direct")
)
```

**Remover ou desligar um elemento sem apagar a linha** — `enabled=False`
mantém nome e arquivo documentados no código, mas exclui o elemento por
completo do cálculo:

```python
OpticalElement(name="Filtro OD 1.3", path=DADOS / "filtro_1_3.csv",
               kind="direct", enabled=False)
```

**Trocar qual curva um elemento usa** — só muda o `path`:

```python
OpticalElement(name="BSW26R dichroic plate",
               path=DADOS / "Figura 42 S-Pol - ....csv", kind="direct")
```

**Comparar "e se eu tirasse esse elemento?"** sem duplicar o script
principal:

```python
sem_fibra = [e for e in elementos if e.name != "1000um fiber"]
_, corrigido_sem_fibra = apply_correction(wl, dn, sem_fibra)
```

**Ajustar idioma e faixa dos gráficos:**

```python
generate_report(wl, dn, elementos, out_dir="resultados_pt",
                lang="pt", xlim=(350, 900))   # lang: "en" ou "pt"; xlim=None = sem limite
```

**Depois de qualquer mudança**, rode os testes e olhe os avisos no console
— eles apontam quando um `kind` ou CSV provavelmente está errado:

```bash
pytest -q
```

### Saída de `generate_report`

```
resultados/
  per_item/
    <slug>_transmittance.png      # curva digitalizada, interpolada no grid do SUNS
    <slug>_suns_corrected.png     # SUNS original vs. corrigido só por ESSE elemento
  combined/
    total_loss.png                          # produto de todos os elementos
    spectrum_original_vs_corrected.png       # original vs. corrigido (tudo aplicado)
    spectrum_original_vs_corrected_log.png   # idem, escala log
    spectrum_normalized.png                  # comparação normalizada
```

(`<slug>` = nome do elemento normalizado — ex.: `"ND filter OD 1.0"` vira
`nd_filter_od_1_0`.)

---

## Referência da API

| Nome | Assinatura | O quê |
|---|---|---|
| `OpticalElement` | `(name, path, kind="direct", percent=True, enabled=True)` | Um elemento óptico digitalizado |
| `.transmittance()` | `(wl_grid, clip=True) -> np.ndarray` | Transmitância interpolada no grid pedido |
| `.data()` | `() -> pd.DataFrame` | A curva crua digitalizada (wavelength, value) |
| `.plot_curve()` | `(out_path, wl_grid=None, lang="en", xlim=None)` | Plota só a curva desse elemento |
| `.slug()` | `() -> str` | Nome normalizado (usado em nomes de arquivo) |
| `read_digitized_csv` | `(path) -> pd.DataFrame` | Lê um CSV digitalizado (qualquer um dos dois formatos) |
| `read_suns_raw` | `(folder, pattern="*.txt") -> pd.DataFrame` | Lê um `.txt` bruto (arquivo único) ou uma pasta deles (faz a média) |
| `read_suns_spectrum` | `(path) -> pd.DataFrame` | Lê um espectro do SUNS já processado (wavelength, dn) |
| `write_corrected_csv` | `(wl, dn, path) -> None` | Salva um espectro (corrigido ou não) como CSV (wavelength, dn) |
| `compute_losses` | `(elements, wl_grid) -> LossResult` | Combina os elementos *enabled* (por item + total) |
| `apply_correction` | `(suns_wl, suns_dn, elements) -> (LossResult, np.ndarray)` | Escolhe o que aplicar: um filtro, vários, ou a calibração total |
| `correct_spectrum` | `(spectrum, transmittance) -> np.ndarray` | `spectrum / transmittance` |
| `generate_report` | `(suns_wl, suns_dn, elements, out_dir, lang="en", xlim=None)` | `apply_correction` + escreve todas as figuras em disco |

`LossResult`: `.wl` (grid usado), `.per_item` (dict nome → transmitância,
só elementos `enabled`), `.total` (produto de todas as transmitâncias).

---

## Testes

```bash
git clone https://github.com/guicavazzana/suns.git
cd suns
pip install -e ".[test]"
pytest -q
```

Os testes não dependem de instalação — `tests/conftest.py` insere `src/`
no `sys.path` diretamente.

---

## Solução de problemas

**`pip install -e .` falhando silenciosamente no Windows** — se o caminho
do projeto tiver acentos (ex.: uma pasta chamada "Dissertação"), o
instalador editável grava um redirecionamento `.pth` que o `site.py` do
Windows lê com o codepage ANSI (cp1252) em vez de UTF-8: o caminho vem
corrompido, `import suns` falha com `ModuleNotFoundError` e nenhum erro é
mostrado. Uma instalação normal (`pip install .`, sem `-e`) copia os
arquivos de verdade e não sofre esse problema.

---

MIT © Guilherme Cavazzana
