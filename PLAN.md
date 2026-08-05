# PLAN — análise tarifa zero domingos: demanda x oferta x gênero/idade

Reorganização em pastas já concluída (`01_criacao_de_bases/`, `02_oferta/`, `03_comparacoes/`, caminhos relativos ajustados, `CLAUDE.md` atualizado com a nova estrutura). Faltam as duas etapas abaixo.

## Etapa 1 — Criar `03_comparacoes/compara_demanda_oferta_genero_idade.ipynb`

Notebook novo, self-contained (não estende `02_cria_base_demanda_mes.ipynb`, cujo agregado line×zona×mês já é consumido por `compara_demanda.ipynb` — mudar esse schema quebraria esse consumidor).

**Seção 0 — imports/config**: `polars`, `pandas`, `geopandas`, `folium`, `branca.colormap`, `shapely.geometry.Point`. `od = 2023`. `MESES = ["04","05","09","10"]` (janela comum às duas bases — decisão já tomada com o usuário).

**Seção 1 — agregado de demanda** (linha × zona × Ano × Mês × tipo_dia × genero × faixa_etaria):
- De `../outputs/Dados_4Meses_2023_2024.parquet`: derivar `tipo_dia` do weekday de `data` (`pl.col("data").str.to_date("%Y%m%d").dt.weekday()`), filtrar `MESES`, **excluir domingos** (weekday==7) para não duplicar com a base de domingos.
- De `../outputs/Dados_Domingos_2023_2024.parquet`: filtrar `MESES`, marcar `tipo_dia="domingo"` (todas as linhas já são domingo por construção).
- Agregar cada fonte por `linha_blt, zona_emb, Ano, Mês, tipo_dia, genero, faixa_etaria` → `N_embarques` (via `pl.len()`, streaming), depois `pl.concat` das duas agregações (não concatenar linhas brutas antes de agregar).
- Persistir como `../outputs/Dados_4Meses_Domingos_2023_2024_genero_idade.parquet`.
- Célula de validação: comparar a proporção util/sábado/domingo derivada do weekday contra a coluna `Tipo Dia` de `Partidas.csv` (mais autoritativa) para linhas/meses em comum; avisar se divergência > 5%.

**Seção 2 — geometria de zonas, ponto de referência do CBD, tiers de periferia**:
- Reusar o toggle `od` e o shapefile de zonas já usado em `compara_demanda.ipynb`.
- Ponto de referência: Praça da Sé, `Point(-46.6333, -23.5505)` em WGS84, reprojetado para o CRS das zonas (confirmar `22523`, já usado em `compara_demanda.ipynb` — reprojetar explicitamente se `zonas.crs` vier geográfico).
- `dist_cbd_km = zonas.centroid.distance(cbd_point) / 1000`.
- Tiers por quartil (`pd.qcut`, 4 grupos: Centro / Intermediário 1 / Intermediário 2 / Periferia).
- Sanity check: tabela de contagem de zonas e distância média por tier + `zonas.plot(column="periferia_tier")`.

**Seção 3 — diffs de demanda por zona, domingo vs útil, isolando o efeito tarifa-zero**:
- Para cada `tipo_dia`, pivot Ano 2023→2024 por zona (soma sobre genero/faixa_etaria, esse corte fica para a Seção 6).
- `PctDiff_domingo` e `PctDiff_util` por zona.
- Métrica-chave: `Sinal_tarifa_zero = PctDiff_domingo - PctDiff_util`.
- Mapas: (a) diff % domingo, (b) diff % útil (controle), (c) `Sinal_tarifa_zero` em folium com `branca.colormap.LinearColormap` divergente vermelho-branco-verde (mesmo padrão de `compara_demanda.ipynb`).
- Estratificar `Sinal_tarifa_zero` por `periferia_tier` (boxplot/barras agrupadas).

**Seção 4 — lado da oferta**: `Partidas.csv` (`E:\SPTrans\pedido 096412- oferta\`) + `Tecnologias.csv` (`F:\SPTrans\pedido 096412- oferta\`, `encoding="latin-1"`).
- Tabela de capacidade nominal por `Tecnologia` (Miniônibus, Midiônibus09/11, Básico, Padron13/14/15, Articulado18/19/20/23, variantes elétricas "e"-prefixadas = mesma capacidade do correspondente a combustão; Embarcacao* excluídas) — célula markdown deixando explícito que são valores públicos aproximados, a validar antes de qualquer conclusão publicada.
- `Capacidade_frota = Frota × capacidade_nominal`, agregado por `Linha × Ano Mês × Tipo Dia`. Print de linhas com `Tecnologia` não mapeada antes de confiar nos totais.
- Proxy de oferta principal: **capacidade de frota** (`Frota × capacidade_nominal`), não partidas × capacidade. `n_partidas` (contagem de `Partidas.csv`) fica como métrica secundária de checagem.
- Mapear valores de `Tipo Dia` (Partidas/Tecnologias) para o vocabulário `tipo_dia` da Seção 1 — checar strings exatas ao carregar, não assumir.
- Join oferta→zona (maior risco do plano): casar `Linha` (Partidas/Tecnologias) com `linha_blt` (demanda) e/ou `line_name` (gpkg de linhas, mesma derivação de `compara_demanda.ipynb`: split de `trip_id` em `-`, duas primeiras partes). Célula de diagnóstico de taxa de match antes de prosseguir. Se taxa alta (>90% ponderado por demanda): join espacial linha×zona (mesmo padrão de overlay de `compara_demanda.ipynb`). Se taxa baixa: fallback explícito para análise em nível de linha.

**Seção 5 — razão lugares ofertados / demanda**: `Ratio = Capacidade_frota / N_embarques` por zona (ou linha, conforme fallback), diff 2023→2024, estratificado por `periferia_tier`, domingo (principal) e útil (controle).

**Seção 6 — recorte por gênero e idade**: usando o agregado completo da Seção 1.
- Crescimento % por zona, por gênero (F vs M), domingo vs útil, mesma lógica de isolamento da Seção 3.
- Idade: bucket `60+` (`'60 a 69'` até `'90 a 99'`) vs `<60`, mesmo cálculo.
- Reportar também números-resumo agregados na cidade toda (não só mapas por zona), dado risco de esparsidade; suprimir/acinzentar zonas com `N_embarques_2023 < 30` nos mapas.

**Seção 7 — mapas e saída**: reusar os padrões de plot de `compara_demanda.ipynb` (matplotlib `cmap="YlOrRd"` para níveis absolutos; folium divergente para diffs/sinais). Manter HTMLs locais ao notebook, **não salvar em `docs/`** por enquanto (análise exploratória).

## Etapa 2 — Atualizar `CLAUDE.md` com o novo notebook

Documentar:
- O novo notebook e sua posição no pipeline (consome `01_criacao_de_bases` diretamente; não depende de `02_cria_base_demanda_mes.ipynb`).
- O novo artefato `outputs/Dados_4Meses_Domingos_2023_2024_genero_idade.parquet` e seu schema.
- A nova fonte `Tecnologias.csv` (encoding latin-1) e a tabela de capacidade nominal como premissa a validar.
- O ponto de referência do CBD (Praça da Sé) e o método de tiers de periferia (quartil de distância) em "Key domain columns".
- A decisão de escopo de meses (abr/mai/set/out, não ano completo).

## Riscos a sinalizar no notebook

1. Join de ID de linha (`linha_blt` vs `Linha` vs `line_name`) entre três sistemas diferentes — diagnóstico de match-rate obrigatório, fallback para nível de linha.
2. Capacidade nominal por tecnologia é aproximação pública, não valor oficial certificado. Diffs ano-a-ano são mais defensáveis que valores absolutos.
3. Esparsidade em cortes zona × gênero × idade × tipo_dia simultâneos — priorizar agregados por tier/cidade.
4. Vocabulário de `Tipo Dia` diferente entre Partidas/Tecnologias e o `tipo_dia` derivado do weekday — mapear explicitamente.
5. Consistência entre a base de Domingos (semanal) e a base de 4-Meses (diária) — documentar como limitação conhecida.

## Verificação

- Célula de validação de `tipo_dia` (Seção 1) sem divergência > 5%.
- Tabela de diagnóstico de match-rate de linha (Seção 4) antes do join espacial.
- Inspecionar visualmente os 3 mapas da Seção 3 e o mapa/tabela da Seção 5 antes de tirar conclusões.
