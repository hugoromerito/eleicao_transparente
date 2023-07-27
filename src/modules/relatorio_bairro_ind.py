# Author: Hugo de Souza de Queiroz (Romerito Queiroz)
# Date: 2023-07-22
# Title: Eleição Transparente
# Description: Neighborhood voting report generation system
# Version: 1.0.0
# License: MIT License

import pandas as pd
import unidecode


def gerar_rel_bairro(candidatos, colegios, municipio_escolhido, nome_escolhido, nomes_urna, saida_rel):

    # Carregar o arquivo da apuracao
    df_candidatos = pd.read_csv(candidatos, sep=';', encoding='ISO-8859-1', quotechar='"')

    # Carregar o arquivo com a lista de colegios
    df_colegios = pd.read_csv(colegios, sep=';', encoding='ISO-8859-1', quotechar='"')

    # Renomear as colunas do DataFrame de "candidatos"
    df_candidatos = df_candidatos.rename(columns={'NR_ZONA': 'ZONA',
                                                  'NR_SECAO': 'SECAO',
                                                  'DS_CARGO_PERGUNTA': 'CARGO',
                                                  'DS_CARGO': 'CARGO',
                                                  'NM_VOTAVEL': 'NOME_CANDIDATO',
                                                  'NM_MUNICIPIO': 'MUNICIPIO',
                                                  'QT_VOTOS': 'VOTOS'})

    # Renomear as colunas do DataFrame de "colegios"
    df_colegios = df_colegios.rename(columns={'NUM_ZONA': 'ZONA',
                                              'SECOES': 'SECAO',
                                              'NOM_BAIRRO': 'BAIRRO'})

    df_candidatos['MUNICIPIO'] = df_candidatos['MUNICIPIO'].apply(lambda x: unidecode.unidecode(x))
    df_candidatos['NOME_CANDIDATO'] = df_candidatos['NOME_CANDIDATO'].apply(lambda x: unidecode.unidecode(x))

    # Converter os valores da coluna 'BAIRRO' para string
    df_colegios['BAIRRO'] = df_colegios['BAIRRO'].astype(str)

    # Substituir os valores NaN da coluna 'BAIRRO' por uma string vazia
    df_colegios['BAIRRO'] = df_colegios['BAIRRO'].replace('nan', '')

    # Aplicar a funcao unidecode para remover acentos e caracteres especiais
    df_colegios['BAIRRO'] = df_colegios['BAIRRO'].apply(lambda x: unidecode.unidecode(x) if isinstance(x, str) else x)

    # Verificar e substituir os nomes de urna no DataFrame
    df_candidatos.loc[df_candidatos['NOME_CANDIDATO'].isin(nomes_urna)
                      & (df_candidatos['NOME_CANDIDATO'] != nome_escolhido), 'NOME_CANDIDATO'] = nome_escolhido


    # Filtrar apenas os seguintes registros
    df_candidatos = df_candidatos[(df_candidatos['MUNICIPIO'] == municipio_escolhido)
                                  & (df_candidatos['NOME_CANDIDATO'] == nome_escolhido)]


    # Realizar o merge dos dataframes utilizando as colunas 'NR_ZONA' e 'NR_SECAO' como chave de junção
    df_merged = pd.merge(df_candidatos, df_colegios, on=['ZONA', 'SECAO'])

    # Agrupar os candidatos por local, bairro, nome do candidato e calcular a soma dos votos
    df_aggregated = df_merged.groupby(['BAIRRO', 'NOME_CANDIDATO']).agg({'VOTOS': 'sum'}).reset_index()

    # Selecionar apenas os campos desejados
    df_resultado = df_aggregated[['BAIRRO', 'NOME_CANDIDATO', 'VOTOS']]

    # Salvar o resultado em um novo arquivo CSV
    df_resultado.to_csv(saida_rel, index=False)


