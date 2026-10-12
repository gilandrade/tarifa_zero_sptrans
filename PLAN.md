# PLAN — análise tarifa zero domingos: demanda x oferta x gênero/idade

## Estado atual

Concluído:

- Reorganização em pastas numeradas por estágio, com `outputs/` também namespaceado por estágio
  (`outputs/01/`, `outputs/02/`, `outputs/03/`).
- `03_comparacoes/compara_demanda_oferta_genero_idade.ipynb` — construído e rodando de ponta a
  ponta, Seções 0 a 8.
- `01_criacao_de_bases/03_cria_base_oficial.ipynb` — série oficial de passageiros transportados,
  **731/731 dias** de 2023-2024 (989.311 registros), com célula de integridade sobre os arquivos
  brutos. O único arquivo corrompido na origem (`20230529.xls`) foi recuperado via Excel.
- `01_criacao_de_bases/04_diagnostico_domingos_antiga_vs_nova.ipynb` — caracterizou a relação entre
  as duas entregas de domingo e validou a base nova contra o oficial.
- `01_criacao_de_bases/05_imputa_zona_domingo.ipynb` — aposentado: a entrega de domingos foi
  reemitida com `zona_emb` nativa (ver item 5).
- `02_oferta/compara_oferta_demanda_agregada.ipynb` — **resultado agregado de oferta × demanda, sem
  recorte espacial**, sobre os 24 meses de 2023-2024. Ver seção dedicada abaixo.
- Migração dos caminhos de origem para `C:\Users\9837292\Desktop\SSD\SPTrans\`, com a constante
  `RAIZ_SPTRANS` no topo de cada notebook que lê dado bruto.
- `CLAUDE.md` atualizado com tudo acima.

O mapa detalhado do pipeline vive no `CLAUDE.md`, não aqui. Este arquivo é só o que ainda falta.

## O que ainda falta

### 1. ~~Publicar / consolidar os resultados~~ — feito

`docs/` agora é um relatório de 3 páginas (`index.html`, `mapas.html`, `metodologia.html`) com os
resultados de `compara_demanda_oferta_genero_idade.ipynb` e `compara_demanda.ipynb`: headline,
gradiente territorial, idade/gênero, oferta, validação e ressalvas, com figuras
(`docs/img/*.png`) e tabelas (`docs/tabelas.js`, gerado por `scripts/gera_tabelas.py` a partir de
`outputs/02/tabelas/` e `outputs/03/tabelas/*.parquet`) — ver "Publicação" no `CLAUDE.md` para o
fluxo completo. O mapa da
Seção 3 (`mapa_sinal_tarifa_zero_zona.html`) saiu de `03_comparacoes/` e foi para `docs/`, onde é
efetivamente publicado.

**Regra que sobreviveu à publicação:** *níveis pela série oficial, desagregação (zona, gênero,
idade) pela bilhetagem.* Medido na Seção 8, com médias por dia e conjuntos de datas corretos por
`tipo_dia`:

| fonte | Δ% domingo | Δ% dia útil | sinal isolado |
|---|---|---|---|
| oficial | +35,95% | +7,03% | **+28,9 p.p.** |
| bilhetagem sem `linha_blt` nula | +27,96% | +4,08% | +23,9 p.p. |

As duas usam o mesmo critério de contagem (sem `linha_blt` nula, médias por dia); a versão bruta,
que incluía os registros sem linha, saiu da tabela publicada — `linha_blt` nula não é embarque de
ônibus municipal, então não é um recorte alternativo, é contagem errada. Mesmo sinal, magnitude
diferente. **No site isso não é apresentado como intervalo de confiança** — as duas são agregações
censitárias, sem amostragem, então erro-padrão/IC não estão definidos; a amplitude é divergência
entre fontes, e o número publicado como manchete é o do oficial (+28,9 p.p.), não uma média ou
faixa das duas.

### 1b. ~~Resultado agregado de oferta × demanda~~ — feito

`02_oferta/compara_oferta_demanda_agregada.ipynb` responde "a oferta acompanhou?" sem nenhum recorte
territorial, e por isso **sem depender de `zona_emb`, sem depender da bilhetagem e sem a janela de 4
meses** — `Partidas.csv` cobre 202301–202412 nos três tipos de dia e a série oficial cobre os 731
dias. Medido, cidade inteira, médias por dia, calendário limpo:

| por dia típico | 2023 | 2024 | Δ% |
|---|---|---|---|
| embarques/domingo (oficial) | 2.145.758 | 2.901.942 | **+35,2%** |
| partidas/domingo | 81.900 | 81.731 | **−0,2%** |
| lugares/domingo | 6.695.412 | 6.703.904 | **+0,1%** |
| lugares por embarque, domingo | 3,12 | 2,31 | **−26,0%** |
| lugares por embarque, dia útil (controle) | 1,97 | 1,91 | −3,1% |

Sinal isolado: **−22,9 p.p.** A métrica em partidas por mil embarques (totalmente observada, sem a
tabela de capacidade) dá −22,7 p.p. — a conclusão não está pendurada em `CAPACIDADE_POR_CATEGORIA`.

Três coisas que este notebook estabeleceu e que valem para o resto do projeto:

1. **A gratuidade dominical começa em 17/12/2023**, lida no colapso de `of_pagantes` (55% → 0,1%
   entre 10 e 17/12). Os três últimos domingos de 2023 são pós-política.
2. **`Partidas.csv` é programação de dia típico**, não do mês — a oferta já é grandeza diária e não
   admite soma entre meses.
3. **Feriados entram no controle de dia útil** se não forem excluídos por lista; junto com três
   domingos anômalos de 2023 (01/10, 05/11, 12/11, ~1/3 do volume normal), a diferença é de 6 p.p.
   no crescimento medido do domingo (+41,6% sem limpeza contra +35,2% com).

Também reconciliou o **+35,95%** publicado na Seção 8 de `compara_demanda_oferta_genero_idade.ipynb`:
aquele número é a série oficial restrita aos **29 domingos que a bilhetagem entregou** dentro dos 4
meses. Sobre todos os domingos dos mesmos meses dá +37,4% limpo / +41,7% bruto — a diferença é
subamostragem de datas, não método.

### 2. Validar a tabela de capacidade nominal

`CAPACIDADE_POR_CATEGORIA` (Seção 4) é aproximação a partir de dado público, não valor oficial
certificado. Enquanto não for validada, só as **variações ano a ano** de capacidade são plenamente
defensáveis. **Esta segue sendo a única razão real da restrição** — não o dia da semana (ver
correção abaixo).

*Ajuste de regra editorial:* o site publica os níveis de `lugares_por_embarque` (3,12 → 2,31)
rotulados como **ordem de grandeza provisória**, com a manchete sendo a variação percentual. O que
justifica ter afrouxado a proibição anterior é que a mesma conta em **partidas por mil embarques** —
contagem direta da programação, sem tabela de capacidade nenhuma — dá o mesmo resultado (−26,2%
contra −26,0%). Se a tabela de capacidade for validada, esses níveis deixam de ser provisórios;
se for refutada, a métrica em partidas sustenta a conclusão sozinha.

**Correção a uma formulação anterior deste risco:** este item costumava dizer que
`Capacidade_ofertada_estimada` "assume" que a composição de frota não muda no domingo, como se
fosse uma suposição não verificável. Não é — a frota é o conjunto físico de veículos cadastrados
na linha, uma propriedade que não muda por ser domingo; o que varia entre tipos de dia é a
frequência, e essa vem de `Partidas.csv`, que cobre `DOMG` explicitamente. A capacidade de domingo
é portanto **inferida** a partir de frequência observada, não suposta.

O resíduo real, agora medido em vez de descartado como "premissa forçada pelo dado, não
verificada" (`outputs/03/tabelas/heterogeneidade_frota.parquet`, Seção 4): **72% das linhas e 83%
do volume de demanda rodam em linhas com mais de uma tecnologia de veículo** — exposição ampla,
não um caso de borda — mas a razão mediana entre a maior e a menor capacidade dentro dessas linhas
mistas é de apenas **1,33×**, o que limita o tamanho do possível viés. Esse viés, além disso,
tende a se repetir em 2023 e 2024 e a se cancelar na diferença entre anos, que é o número
publicado.

### 3. ~~Melhorar o join oferta → zona~~ — causa identificada

Os **73,2%** de match ponderado por demanda que mantinham `USAR_JOIN_ESPACIAL=False` eram artefato
do denominador: `demanda_por_linha` incluía os registros com `linha_blt` nula (26,8% do volume), que
por definição não casam com linha nenhuma. Sobre o volume **com** linha o match é **100,00%**
(1.324 de 1.326 linhas; ficam de fora só `808U-10` e `909K-10`). Não há linha renomeada nem recorte
de datas a investigar — a oferta por zona está destravada e entra no item 6.

### 4. Entender as linhas persistentemente divergentes do oficial

A validação por linha da Seção 8 fecha bem (96,8% das linhas e 93,3% do volume dentro de ±10%),
mas sobra um conjunto pequeno, estável e identificável de linhas que rodam ~1,3–1,45x o oficial
nos **dois** anos: `209P-10`, `8700-10`, `5110-10`. Por serem consistentes, provavelmente é
diferença de contabilidade (linha operada em conjunto? código reaproveitado?), não ruído. Vale
identificar antes de qualquer conclusão por linha.

### 5. ~~Reduzir a dependência de estimativa no domingo~~ — superado

A SPTrans reemitiu a entrega de domingos com `zona_emb` nativa (387 zonas; `999` em 0,11% das
linhas, todas com `linha_blt` nula). A imputação (`05_imputa_zona_domingo.ipynb`) foi aposentada e
as versões por `linha_blt` que acompanhavam cada leitura por zona saíram das Seções 3 e 6. O que
resta é a ressalva de que `zona_emb` é estimativa da própria SPTrans.

### 6. Correlatos do sinal por zona e classificação das linhas

Cruzar o `Sinal_tarifa_zero` por zona OD com características da zona, e classificar as linhas pelos
grupos de lote. Decisões tomadas em 09/10/2026: corte de base mínima pelo **p05 do dia médio da zona
em 2023** (útil + sábado + domingo); oferta por zona pelas **linhas cujo traçado cruza a zona**;
distância de rede via **r5py**; nada novo entra em `docs/` por enquanto.

| # | Tarefa | Onde | Estado |
|---|---|---|---|
| 6.1 | Universo só com zonas do município de São Paulo (`NumeroMuni == 36`); quintis de renda recortados sobre essas zonas | `06`, notebook principal, `compara_demanda` | **feito** — 339 zonas; quintis 68/68/67/68/68; 20 zonas (5,9%) mudaram de quintil |
| 6.2 | Corte p05 no lugar de `N_MIN_ZONA = 500`; exportar `outputs/03/sinal_zona.parquet` | notebook principal, Seção 3 | **feito** — corte 2.081 embarques/dia médio, 17 zonas suprimidas, 322 na análise |
| 6.3 | Classificação das linhas (Estrutural / Articulação Regional / Distribuição Local) e sinal por grupo | `01/07_cria_base_grupo_linha.ipynb`, Seções 3 e 8 | **feito** — 1.469 linhas; sinal 27,9 / 28,5 / 19,1 p.p. (bilhetagem), 34,2 / 35,4 / 22,4 (oficial) |
| 6.4 | % de pessoas negras e distância euclidiana à estação de trem/metrô mais próxima | `01/08_cria_base_covariaveis_zona.ipynb` | **feito** — município 43,51% negros, bate com as zonas; 198 paradas de trilho |
| 6.5 | Partidas e lugares por zona (linhas que cruzam a zona) | notebook principal, Seção 4 | **feito** — match de linhas 100% (o 73,2% era artefato); soma entre zonas = 9,8× o total da cidade |
| 6.6 | Gráficos XY do sinal contra cada variável e mapas das variáveis | `04_correlatos/correlatos_sinal_zona.ipynb` | **feito** — saídas em `outputs/04/` |
| 6.7 | Distância de rede (R5) do centroide da zona à estação mais próxima | `01/09_cria_base_dist_rede_estacao.ipynb` | **feito** — r5py 1.1.7; circuidade mediana 1,31 |

Medido: das 355 zonas com demanda, 339 são de São Paulo; as 16 de municípios vizinhos somam 0,42%
do volume. O p05 do dia médio tira 17 das 339 zonas (0,29% do volume) — o corte anterior tirava 2.

**O que os gráficos mostram** (MQO simples, 322 zonas, sem ponderar por população; a distância em linha
reta saiu da análise): por dobra das partidas por domingo o sinal cai 3,1 p.p. (IC95 −4,7 a −1,5), dos
lugares 2,0 (−3,5 a −0,4) e a cada +1 km de distância pela rede à estação 1,0 (−1,7 a −0,3); renda
(−1,1 por dobra, IC inclui zero) e % de pessoas negras (+0,3 por +10 p.p.) não se distinguem de zero.
O R² não passa de 3,9%. Renda e % de negros são quase a mesma variável (r = −0,91). São associações
entre zonas, não efeito. **As zonas não são independentes** (Moran's I do sinal 0,48, p = 0,001; dos
resíduos 0,46–0,49), então os intervalos estão otimistas.

**Pontas soltas deste bloco:**

- Seis linhas grandes migraram de lote em 2024 (`D10` → `AR6`/`E05`/`E06`); o grupo delas é o dominante
  em volume, e `mudou_grupo` as marca. Se o recorte por grupo virar resultado publicado, decidir se
  essas linhas entram pelo grupo de 2024 em vez do dominante.
- O sinal por grupo pela bilhetagem fica 3–7 p.p. abaixo do oficial em todos os grupos (a mesma
  subestimação do total da cidade); vale o mesmo cuidado de citar níveis pelo oficial.
- ~~**Inferência espacial.**~~ Feita em `04_correlatos/regressao_espacial_sinal.ipynb` (erro, defasagem, Durbin,
  GWR/MGWR; ver item 8). Ponderar pela população da zona continua em aberto.
- Variáveis a mais no eixo x: ver o item 8 (o item "partidas por morador" saiu: o problema era o tamanho da base de
  domingo, que agora entra como controle).

### 7. ~~Republicar o site com o novo universo de zonas~~ — feito em 11/10/2026

`docs/` regenerado (figuras, mapas, `tabelas.js`) e páginas revisadas: texto do território, subseção de grupos de lote,
nova seção 5 de correlatos, metodologia e `mapas.html`. Falta commitar e publicar.

Acrescentado em 12/10/2026 (ainda sem commit): na seção 5 de `index.html`, as subseções "Regressão espacial" e "Coeficientes
que variam no território (MGWR)", com `img/mgwr_coef_locais.png` e três tabelas novas em `tabelas.js`
(`regressao_espacial_publicada`, `mgwr_escalas`, `mgwr_comparacao`); um item na metodologia; dois parágrafos antigos da seção 5
apontam para a regressão espacial, porque a oferta deixa de ser significativa quando a base de domingo entra no modelo.

### 8. Regressão espacial e novas variáveis explicativas

**Feito (11–12/10/2026):** `04_correlatos/regressao_espacial_sinal.ipynb`, uma só especificação ("D"): desfecho = variação %
do embarque médio de domingo 2023 → 2024; controles = variação % do dia útil (peso livre, deu 1,06), log2 da base de domingo
de 2023, log2 da renda, partidas em milhares, distância de rede em km. Modelos globais (MQO + LM, SEM, SAR, SDM) e GWR/MGWR.
Resultado resumido: base e renda significativas; oferta e distância não; os testes LM e o AIC favorecem a defasagem; o MGWR dá
escala global à base e às partidas e escala local (~20% das zonas) à renda e à distância. Números completos no `CLAUDE.md`.

**A fazer: testar mais variáveis**, escolhidas pelo que a literatura usa em modelos de demanda de transporte coletivo por área
(meta-análises de ambiente construído e uso de transporte, estudos de Toronto, Waterloo e Xangai, trabalhos brasileiros sobre zonas
de tráfego) e pelo que já temos em casa. Todas em nível **pré-política (2023)**, para não contaminar o desfecho.

| # | Variável | Fonte | Como construir | Cuidados |
|---|---|---|---|---|
| 8.1 | Automóveis (e motos) por domicílio; % de domicílios sem automóvel | O-D 2023: `Banco2023_divulgacao_310125.csv` (`qt_auto`, `qt_moto`, `zona`, `Fe_dom`) | Média ponderada por `Fe_dom`, por zona de residência | Anda com a renda; parcialmente endógena à oferta de transporte; usar motos à parte |
| 8.2 | % das viagens feitas de ônibus (uso prévio) | O-D 2023 (`modoprin`, `zona_o`, `fe_via`) | Parcela ponderada por `fe_via`, por zona de origem | Base teórica: onde o uso já era alto, o efeito da tarifa zero é menor (Cats et al. 2017, Hess 2017, citados por Perez e Pereira 2025); a pesquisa é de dia útil |
| 8.3 | Parcela de embarques **pagantes** em 2023 (comum, VT, dinheiro, contra idoso e PCD) | Bilhetagem de domingos 2023 (`classificacao`) | Parcela, não soma; só embarques com `linha_blt` | Ideia própria, não vem da busca de literatura: mede quanto da demanda tinha algo a ganhar com a gratuidade |
| 8.4 | Densidade populacional e população absoluta | Censo 2022 (`pop` já está na base) ÷ área da zona | Entrar as duas juntas | Em zonas grandes a densidade esconde o total |
| 8.5 | Destinos de domingo e uso misto (comércio, lazer/parques, equipamentos religiosos, entropia), densidade de interseções | OSM (`Dados/r5/sao_paulo/sao_paulo.osm.pbf`) | Contagens por zona via `pyogrio`; entropia de uso | Liga com o texto da Outras Palavras sobre ambiente de caminhada; efeitos em fim de semana são não lineares |
| 8.6 | Acessibilidade a oportunidades por transporte público | r5py + GTFS (já montados no `09`) com destinos do OSM | Matriz zona × destino por tempo | Custo alto; só se 8.1–8.5 não bastarem |

Ordem sugerida: **8.1, 8.2, 8.4** (dados já em casa, nenhum download), depois **8.3**, **8.5** e, só se preciso, **8.6**.
Procedimento: uma de cada vez na especificação D, comparando o AIC do erro e da defasagem; checar VIF e o Moran do resíduo
filtrado; manter poucas variáveis (a meta-análise mostra que o desenho do modelo explica mais de 40% da variação dos achados).
Atualizar o site só se uma variável nova mudar a conclusão.

## Riscos permanentes a sinalizar em qualquer publicação

1. Capacidade nominal por tecnologia é aproximação pública, não valor oficial certificado — é essa
   a razão de os níveis absolutos de lugares saírem rotulados como provisórios e de a manchete ser a
   variação percentual, não o dia da semana. A métrica paralela em partidas por mil embarques não
   depende dessa tabela e concorda com ela.
2. `Tecnologias.csv` só cobre `UTIL`, mas a capacidade de domingo é **inferida** (frequência
   observada de `Partidas.csv` × composição de frota, que não muda por ser domingo), não suposta.
   O resíduo real — 72% das linhas e 83% do volume em linhas de frota mista, razão mediana de
   capacidade 1,33× dentro delas — está medido em `heterogeneidade_frota`.
3. `zona_emb` é estimativa da SPTrans mesmo quando original; no domingo é imputada por cima disso.
4. A bilhetagem subestima o crescimento do domingo em relação ao oficial (razão escorrega de ~1,05
   para ~0,99 entre os anos).
5. Esparsidade em cortes zona × gênero × idade × tipo_dia simultâneos — daí a supressão por base
   mínima nos mapas e a prioridade aos agregados por tier e cidade.
