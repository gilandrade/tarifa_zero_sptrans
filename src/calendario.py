"""Calendario comum da comparacao ano a ano (Tarifa Zero aos domingos).

Usado por `02_oferta/compara_oferta_demanda_agregada.ipynb` (serie oficial, 12 meses) e por
`03_comparacoes/compara_demanda_oferta_genero_idade.ipynb` (bilhetagem, abr/mai/set/out). As duas
comparacoes precisam excluir as mesmas datas; por isso a lista mora aqui, e nao em cada notebook.

Os notebooks rodam com cwd = a propria pasta de estagio, entao importam com
`sys.path.insert(0, "../src")`.

Datas sempre como string AAAAMMDD. Motivos de exclusao (`motivos_calendario`):

- feriado: nacionais, estaduais (SP) e municipais (cidade de SP), excluidos mesmo no fim de
  semana, para o criterio ser simetrico, exceto os feriados com tarifa zero a partir do inicio
  da politica, que contam como domingo (tratamento).
- ponte: dia util colado a feriado (sexta depois de quinta, segunda antes de terca), com
  ~0,75-0,80 da mediana do dia util, que a regra de outlier de 60% nao pega.
- atipico: vespera de Natal e de Ano Novo, 02/01 e quarta-feira de cinzas.
- eleicao: domingos de eleicao (voto obrigatorio), com ~1,3x a mediana do domingo. A entrega da
  bilhetagem nao traz os de 2024, mas a serie oficial traz.
- fim_de_ano: 17 a 31/12 de todo ano. Em 2023 esses dias ja sao tratados (a politica comeca em
  17/12/2023); exclui-los so em 2023 deixaria dezembro de 2023 com a primeira quinzena e os
  outros anos com o mes inteiro, incluindo as compras de Natal e o recesso.
"""

DATA_INICIO_POLITICA = "20231217"  # colapso de of_pagantes no domingo, ver o notebook agregado

# Moveis (Carnaval, Sexta-feira Santa, Corpus Christi) calculados a partir da Pascoa de cada ano.
# 09/07 = Revolucao Constitucionalista (estadual); 25/01 = aniversario da cidade; 20/11 = Consciencia Negra.
FERIADOS = {
    "2023": ["0101", "0125", "0220", "0221", "0407", "0421", "0501", "0608",
             "0709", "0907", "1012", "1102", "1115", "1120", "1225"],
    "2024": ["0101", "0125", "0212", "0213", "0329", "0421", "0501", "0530",
             "0709", "0907", "1012", "1102", "1115", "1120", "1225"],
    "2025": ["0101", "0125", "0303", "0304", "0418", "0421", "0501", "0619",
             "0709", "0907", "1012", "1102", "1115", "1120", "1225"],
    "2026": ["0101", "0125", "0216", "0217", "0403", "0421", "0501", "0604",
             "0709", "0907", "1012", "1102", "1115", "1120", "1225"],
}

# Feriados em que a prefeitura tambem aplica tarifa zero (fora do domingo), so a partir de
# DATA_INICIO_POLITICA.
FERIADOS_TARIFA_ZERO_MMDD = {"0101", "0125", "1225"}

# Levantadas na serie oficial (dia util vizinho de feriado com menos de 0,90 da mediana do ano).
PONTES = {
    "2023": ["0609", "0908", "1013", "1103"],
    "2024": ["0126", "0531", "0708"],
    "2025": ["0502", "0620", "1121"],
    "2026": ["0420"],
}

# Vesperas, 02/01 e quarta-feira de cinzas (expediente reduzido).
ATIPICOS = {
    "2023": ["0102", "0222", "1224", "1231"],
    "2024": ["0102", "0214", "1224", "1231"],
    "2025": ["0102", "0305", "1224", "1231"],
    "2026": ["0102", "0218", "1224", "1231"],
}

ELEICOES = {"20241006", "20241027", "20261004", "20261025"}

FIM_DE_ANO_MMDD = ("1217", "1231")  # inclusive, em todo ano

# Dias em que a entrega da bilhetagem veio truncada: razao bilhetagem/oficial do dia abaixo de
# 0,90 (13/04/2024: 0,39; 14/04/2024: 0,76; nos demais dias entregues fica entre 0,98 e 1,06).
# O notebook de comparacoes recalcula a regra e confere que acha exatamente estas datas; o
# notebook agregado as usa so na checagem cruzada com ele.
LIMIAR_DEFEITO_ENTREGA = 0.90
DATAS_DEFEITO_BILHETAGEM = {"20240413", "20240414"}

LIMIAR_OUTLIER = 0.60  # fracao da mediana do proprio tipo_dia/ano, para dias "normais"


def _expande(por_ano):
    return {ano + mmdd for ano, ds in por_ano.items() for mmdd in ds}


DATAS_FERIADO_TARIFA_ZERO = {
    d for d in _expande(FERIADOS)
    if d[4:] in FERIADOS_TARIFA_ZERO_MMDD and d >= DATA_INICIO_POLITICA
}
DATAS_FERIADO = _expande(FERIADOS) - DATAS_FERIADO_TARIFA_ZERO
DATAS_PONTE = _expande(PONTES)
DATAS_ATIPICAS = _expande(ATIPICOS)


def eh_fim_de_ano(data):
    return FIM_DE_ANO_MMDD[0] <= data[4:] <= FIM_DE_ANO_MMDD[1]


def motivos_calendario(data):
    """Motivos de calendario para excluir `data` (AAAAMMDD) da comparacao ano a ano.

    Args:
        data: data como string AAAAMMDD.

    Returns:
        Lista de motivos ("feriado", "ponte", "atipico", "eleicao", "fim_de_ano"); vazia se o
        dia entra na comparacao. Feriados com tarifa zero nao sao motivo (contam como domingo),
        mas caem em "fim_de_ano" quando sao 25/12.
    """
    motivos = []
    if data in DATAS_FERIADO:
        motivos.append("feriado")
    if data in DATAS_PONTE:
        motivos.append("ponte")
    if data in DATAS_ATIPICAS:
        motivos.append("atipico")
    if data in ELEICOES:
        motivos.append("eleicao")
    if eh_fim_de_ano(data):
        motivos.append("fim_de_ano")
    return motivos


def marca_outlier(df, col_valor, col_grupo, normal):
    """Marca dias abaixo de LIMIAR_OUTLIER x a mediana dos dias normais do mesmo grupo.

    Args:
        df: DataFrame com um dia por linha.
        col_valor: coluna com o volume do dia.
        col_grupo: colunas que definem o grupo da mediana (ex.: ["Ano", "tipo_dia"]).
        normal: Series booleana, True nos dias que entram na mediana de referencia.

    Returns:
        Series booleana alinhada a `df`; so dias normais podem ser outlier.
    """
    mediana = df[normal].groupby(col_grupo)[col_valor].median().rename("_mediana")
    ref = df[col_grupo].merge(mediana, left_on=col_grupo, right_index=True, how="left")["_mediana"]
    return normal & (df[col_valor] < LIMIAR_OUTLIER * ref.to_numpy())
