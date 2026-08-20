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
- `01_criacao_de_bases/05_imputa_zona_domingo.ipynb` — **`zona_emb` do domingo imputada**
  (cobertura ~99% do volume com linha), o que devolveu a análise por zona ao dia da política.
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

### 3. Melhorar o join oferta → zona

A taxa de match `linha_blt` × `Linha` é de 1317/1327 linhas distintas mas só **73,2% do volume
ponderado por demanda**, abaixo do limiar de 90% — então `USAR_JOIN_ESPACIAL=False` e a alocação
espacial linha→zona não roda. Investigar de onde vêm os 27% de volume sem correspondência
(linhas renomeadas no período? recorte de datas?) destravaria a análise de oferta por zona, que
hoje não existe.

### 4. Entender as linhas persistentemente divergentes do oficial

A validação por linha da Seção 8 fecha bem (96,8% das linhas e 93,3% do volume dentro de ±10%),
mas sobra um conjunto pequeno, estável e identificável de linhas que rodam ~1,3–1,45x o oficial
nos **dois** anos: `209P-10`, `8700-10`, `5110-10`. Por serem consistentes, provavelmente é
diferença de contabilidade (linha operada em conjunto? código reaproveitado?), não ruído. Vale
identificar antes de qualquer conclusão por linha.

### 5. Reduzir a dependência de estimativa no domingo

`zona_emb` no domingo é estimativa sobre estimativa: a SPTrans já a deriva de GPS × endereço
cadastrado × horário, e por cima disso vem a imputação. Além disso ~26–33% do volume imputado sai
de pares `(hash, linha)` com mais de uma zona no doador. O caminho definitivo é a **SPTrans
reenviar a entrega de domingos com `zona_emb` preenchido** — enquanto isso não acontece, toda
leitura por zona no domingo anda de par com a versão por `linha_blt` (unidade observada), que as
Seções 3 e 6 mantêm ao lado.

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
