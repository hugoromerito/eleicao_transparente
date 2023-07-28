# Author: Hugo de Souza de Queiroz (Romerito Queiroz)
# Date: 2023-07-22
# Title: Eleição Transparente
# Description: Neighborhood voting report generation system
# Version: 1.0.0
# License: MIT License

import pandas as pd
import unidecode
import matplotlib.pyplot as plt


# Carrega os arquivos com os dados da apuracao e da lista de colegios
# Separa a quantidade de votos do candidato por bairro
# Realiza
def gerar_rel_rank_bairro(zone_votes,
                          schools,
                          county,
                          selected_name,
                          urn_names,
                          office,
                          result_ranking_nbhd,
                          result_ranking_nbhd_graph):

    # Carregar arquivo da apuracao
    df_zone_votes = pd.read_csv(zone_votes, sep=';', encoding='ISO-8859-1', quotechar='"')

    # Carregar arquivos com a lista de colegios
    df_schools = pd.read_csv(schools, sep=';', encoding='ISO-8859-1', quotechar='"')

    # Renomear as colunas do DataFrame de "candidatos"
    df_zone_votes = df_zone_votes.rename(columns={'NR_ZONA': 'ZONA',
                                                  'NR_SECAO': 'SECAO',
                                                  'DS_CARGO_PERGUNTA': 'CARGO',
                                                  'DS_CARGO': 'CARGO',
                                                  'NM_VOTAVEL': 'NOME_CANDIDATO',
                                                  'NM_MUNICIPIO': 'MUNICIPIO',
                                                  'QT_VOTOS': 'VOTOS'})

    # Renomear as colunas do DataFrame de "colegios"
    df_schools = df_schools.rename(columns={'NUM_ZONA': 'ZONA',
                                            'SECOES': 'SECAO',
                                            'NOM_BAIRRO': 'BAIRRO'})

    df_zone_votes['MUNICIPIO'] = df_zone_votes['MUNICIPIO'].apply(lambda x: unidecode.unidecode(x))
    df_zone_votes['NOME_CANDIDATO'] = df_zone_votes['NOME_CANDIDATO'].apply(lambda x: unidecode.unidecode(x))
    df_zone_votes['CARGO'] = df_zone_votes['CARGO'].str.upper()

    # Converter e os valores da coluna 'BAIRRO' para string
    # Substitui os valores NaN por uma string vazia
    # E aplica a funcao unidecode para remover acentos e caracteres especiais
    df_schools['BAIRRO'] = df_schools['BAIRRO'].astype(str)
    df_schools['BAIRRO'] = df_schools['BAIRRO'].replace('nan', '')
    df_schools['BAIRRO'] = df_schools['BAIRRO'].apply(lambda x: unidecode.unidecode(x) if isinstance(x, str) else x)

    # Verificar e substituir os nomes de urna no DataFrame
    df_zone_votes.loc[df_zone_votes['NOME_CANDIDATO'].isin(urn_names)
                      & (df_zone_votes['NOME_CANDIDATO'] != selected_name), 'NOME_CANDIDATO'] = selected_name

    # Eliminar os votos nulos e brancos
    df_zone_votes = df_zone_votes[~df_zone_votes['NOME_CANDIDATO'].isin(['VOTO NULO', 'VOTO BRANCO', 'Branco', 'Nulo'])]

    # Filtrar apenas os seguintes registros
    df_zone_votes = df_zone_votes[(df_zone_votes['MUNICIPIO'] == county) &
                                  (df_zone_votes['CARGO'] == office)]

    # Realizar o merge dos dataframes utilizando as colunas 'NR_ZONA' e 'NR_SECAO' como chave de juncao
    df_merged = pd.merge(df_zone_votes, df_schools, on=['ZONA', 'SECAO'])

    # Agrupar os candidatos por local, bairro, nome do candidato e calcular a soma de votos
    df_aggregated = df_merged.groupby(['BAIRRO', 'NOME_CANDIDATO']).agg({'VOTOS': 'sum'}).reset_index()

    # Ordenar os candidatos dentro de cada bairro por quantidade de votos em ordem decrescente
    df_sorted = df_aggregated.sort_values(['BAIRRO', 'VOTOS'], ascending=[True, False])

    # Selecionar apenas os 3 candidatos mais votados de cada bairro
    df_top_three = df_sorted.groupby('BAIRRO').head(3)

    # Selecionar apenas os campos desejados
    df_resultado = df_top_three[['BAIRRO', 'NOME_CANDIDATO', 'VOTOS']]

    # Filtrar apenas os bairros com o NOME_CANDIDATO_ESCOLHIDO
    df_filter_candidate = df_resultado[df_resultado['NOME_CANDIDATO'] == selected_name]

    # Filtrar apenas os bairros com o NOME_CANDIDATO_ESCOLHIDO
    df_filter_neighborhood = df_filter_candidate['BAIRRO'].unique()

    df_filtered = df_resultado[df_resultado['BAIRRO'].isin(df_filter_neighborhood)]

    # Salvar o resultado em um novo arquivo CSV
    df_filtered.to_csv(result_ranking_nbhd, index=False)

    df_pivot = df_filtered.pivot(index='BAIRRO', columns='NOME_CANDIDATO', values='VOTOS').fillna(0)

    df_pivot.plot(kind='bar', stacked=False, figsize=(15, 10))
    plt.xlabel('Bairro')
    plt.ylabel('Votos')
    plt.title('Votos de cada candidato por bairro (apenas bairros onde o candidato está presente)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.legend(title='Candidatos')
    plt.savefig(result_ranking_nbhd_graph, format='png', dpi=300)
    plt.close()

