# PLAN — análise tarifa zero domingos: demanda x oferta x gênero/idade

## Estado atual

Concluído:

- Reorganização em pastas numeradas por estágio, com `outputs/` também namespaceado por estágio
  (`outputs/01/`, `outputs/03/`).
- `03_comparacoes/compara_demanda_oferta_genero_idade.ipynb` — construído e rodando de ponta a
  ponta, Seções 0 a 8.
- `01_criacao_de_bases/03_cria_base_oficial.ipynb` — série oficial de passageiros transportados,
  **731/731 dias** de 2023-2024 (989.311 registros), com célula de integridade sobre os arquivos
  brutos. O único arquivo corrompido na origem (`20230529.xls`) foi recuperado via Excel.
- `01_criacao_de_bases/04_diagnostico_domingos_antiga_vs_nova.ipynb` — caracterizou a relação entre
  as duas entregas de domingo e validou a base nova contra o oficial.
- `01_criacao_de_bases/05_imputa_zona_domingo.ipynb` — **`zona_emb` do domingo imputada**
  (cobertura ~99% do volume com linha), o que devolveu a análise por zona ao dia da política.
- Migração dos caminhos de origem para `C:\Users\9837292\Desktop\SSD\SPTrans\`, com a constante
  `RAIZ_SPTRANS` no topo de cada notebook que lê dado bruto.
- `CLAUDE.md` atualizado com tudo acima.

O mapa detalhado do pipeline vive no `CLAUDE.md`, não aqui. Este arquivo é só o que ainda falta.

## O que ainda falta

### 1. Publicar / consolidar os resultados

O notebook de gênero/idade continua exploratório: os mapas ficam locais a `03_comparacoes/` e não
vão para `../docs/`. Falta decidir o recorte que vira resultado publicável e escrever a narrativa
com as ressalvas metodológicas já levantadas.

**Regra que precisa sobreviver a qualquer publicação:** *níveis pela série oficial, desagregação
(zona, gênero, idade) pela bilhetagem.* Medido na Seção 8, com médias por dia e conjuntos de datas
corretos por `tipo_dia`:

| fonte | Δ% domingo | Δ% dia útil | sinal isolado |
|---|---|---|---|
| oficial | +35,95% | +7,03% | **+28,9 p.p.** |
| bilhetagem sem `linha_blt` nula | +27,96% | +4,08% | +23,9 p.p. |
| bilhetagem como as seções calculam | +20,87% | +5,74% | +15,1 p.p. |

Mesmo sinal, magnitude diferente — a diferença é a margem de incerteza, e precisa ser declarada.

### 2. Validar a tabela de capacidade nominal

`CAPACIDADE_POR_CATEGORIA` (Seção 4) é aproximação a partir de dado público, não valor oficial
certificado. Enquanto não for validada, só as **diferenças ano a ano** de capacidade são
defensáveis; nenhum número absoluto de lugares ofertados deve ser publicado.

Some-se a isso que `Tecnologias.csv` só traz linhas `UTIL`: a composição de frota por tecnologia é
conhecida apenas para dia útil, e `Capacidade_ofertada_estimada` assume que ela não muda em
sábado/domingo (só a frequência muda). Premissa forçada pela disponibilidade do dado, não
verificada.

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

1. Capacidade nominal por tecnologia é aproximação pública, não valor oficial certificado.
2. `Tecnologias.csv` só cobre `UTIL` — capacidade média por veículo assumida constante entre tipos
   de dia.
3. `zona_emb` é estimativa da SPTrans mesmo quando original; no domingo é imputada por cima disso.
4. A bilhetagem subestima o crescimento do domingo em relação ao oficial (razão escorrega de ~1,05
   para ~0,99 entre os anos).
5. Esparsidade em cortes zona × gênero × idade × tipo_dia simultâneos — daí a supressão por base
   mínima nos mapas e a prioridade aos agregados por tier e cidade.
