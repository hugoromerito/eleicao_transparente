# Author: Hugo de Souza de Queiroz (Romerito Queiroz)
# Date: 2023-07-22
# Title: Eleição Transparente
# Description: Neighborhood voting report generation system
# Version: 1.0.0
# License: MIT License

import re
import threading
import webbrowser
from tkinter import *
from PIL import Image
import CTkMessagebox as CTkMessagebox
import customtkinter as ctk
import pandas as pd
from CTkListbox import CTkListbox
from unidecode import unidecode
from src.styles.color_palette import colors
from src.modules.counties import county_list
from src.modules.ctk_scrollable_dropdown import CTkScrollableDropdown
from src.modules.relatorio_bairro_ind import gerar_rel_bairro
from src.modules.relatorio_rank_bairro import gerar_rel_rank_bairro

# Setando a aparecnia padrao do sistema
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


# Classe da janela pop-up de confirmação do nome do candidato
class MyCTkToplevel(ctk.CTkToplevel):
    def __init__(self, *args, **kwargs):
        self.pending_events = []
        super().__init__(*args, **kwargs)  # Moved to the end of __init__

    def after(self, ms, func=None, *args):
        event_id = super().after(ms, func, *args)
        self.pending_events.append(event_id)
        return event_id

    def destroy(self):
        # Cancel all pending events
        for event_id in self.pending_events:
            self.after_cancel(event_id)
        # Call the superclass destroy method
        super().destroy()


# Janela principal do sistema
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.layout_config()
        self.appearance()
        self.system_app()
        self.footer()
        self.cpf_formatted = False
        self.name_formatted = False

    # Configurando o layout
    def layout_config(self):
        self.title("Eleição Transparente")
        self.geometry("900x500")
        self.configure(fg_color=[colors['background_first_light'], colors['background_first_dark']])
        self.resizable(False, False)

    # Criando o menu de tema
    def appearance(self):
        self.lb_apm = ctk.CTkLabel(self,
                                   text="Tema",
                                   bg_color="transparent",
                                   text_color=["#000", "#fff"]
                                   ).place(x=50, y=420)

        # Criando o menu de opcoes de tema
        self.opt_apm = ctk.CTkOptionMenu(self,
                                         values=["System", "Dark", "Light"],
                                         command=self.change_apm
                                         ).place(x=50, y=450)

    # Formatação do campo CPF
    def format_cpf(self, *args):
        value = self.cpf_var.get()
        new_value = ''.join(filter(str.isdigit, value))  # Remove non-digit characters

        if len(new_value) > 11:
            new_value = new_value[:11]

        # Formata o campo quando todos os 11 digitos sao inseridos
        if len(new_value) == 11:
            # Remove temporariamente a validacao
            self.cpf_entry.configure(validate="none")
            formatted = '{}.{}.{}-{}'.format(new_value[:3], new_value[3:6], new_value[6:9], new_value[9:])
            self.cpf_var.set(formatted)                 # Update the cpf_var
            self.cpf_entry.icursor(END)                 # Move cursor para o final
            self.cpf_entry.configure(validate="key")    # Disable the cpf_entry
            self.cpf_formatted = True                   # Define a flag to indicate that the CPF is formatted
            self.focus()                                # Move focus away from the cpf_entry

            # restore validation after a small delay (to avoid a potential race condition)
            self.after(10, lambda: self.cpf_entry.configure(validate="key"))
        else:
            if self.cpf_formatted:
                # If the user deletes characters and the CPF was already formatted, re-enable the entry
                self.cpf_var.set(new_value)
                self.cpf_formatted = False  # Reset the flag when user removes formatting
        validate_cmd_cpf = self.register(lambda value: value == "" or value.isdigit())
        self.name_entry.configure(validate="key", validatecommand=(validate_cmd_cpf, "%P"))

    # Formatação do campo NOME
    def format_entry_name(self, *args):
        value = self.name_var.get()
        new_value = unidecode(value).upper()  # Remove accents
        self.name_var.set(new_value)

    # Formatação do campo OUTPUT_FILE_NAME
    def format_entry_output(self, *args):
        value = self.output_file_name_var.get()
        new_value = unidecode(value).upper()
        new_value = new_value.replace(' ', '_')     # Remove accents
        self.output_file_name_var.set(new_value)

    # Validação do campo NOME
    def validate_entry_name(self, value):
        return all(c.isalpha() or c.isspace() for c in value) or value == ""

    # Validação do campo OUTPUT_FILE_NAME
    def validate_entry_output(self, value):
        return all(c.isalpha() or c.isspace() or c == "_" for c in value) or value == ""

    def validate_entry_cpf(self, value):
        return all(c.isdigit() for c in value) or value == ""

    def create_ctk_combobox(parent, state, justify, command, scrollbar_autocomplete, width, height, values, set_value, dropdown=False):
        combobox = ctk.CTkComboBox(parent,
                                   font=("Inter", 14),
                                   state=state,
                                   cursor="hand2",
                                   command=command,
                                   justify=justify,
                                   height=height,
                                   width=width,
                                   values=values,
                                   fg_color=[
                                       colors['background_first_light'],
                                       colors['background_first_dark']
                                   ],
                                   border_color=[
                                       colors['border_input_text_light'],
                                       colors['border_input_text_dark']
                                   ],
                                   button_color=[
                                       colors['border_input_text_light'],
                                       colors['border_input_text_dark']
                                   ])

        if dropdown:
            scrollable_dropdown = CTkScrollableDropdown(combobox,
                                                        font=("Inter", 14),
                                                        values=values,
                                                        frame_corner_radius=5,
                                                        justify=justify,
                                                        scrollbar=scrollbar_autocomplete,
                                                        autocomplete=scrollbar_autocomplete,
                                                        alpha=1,
                                                        frame_border_color=[
                                                            colors['border_input_text_light'],
                                                            colors['border_input_text_dark']
                                                        ],
                                                        button_color=[
                                                            colors['background_first_light'],
                                                            colors['background_first_dark']
                                                        ],
                                                        hover_color=[
                                                            colors['options_combobox_light'],
                                                            colors['options_combobox_dark']
                                                        ],
                                                        fg_color=[
                                                            colors['background_first_light'],
                                                            colors['background_first_dark']
                                                        ],
                                                        scrollbar_button_color=[
                                                            colors['border_input_text_light'],
                                                            colors['border_input_text_dark']
                                                        ],
                                                        scrollbar_button_hover_color=[
                                                            colors['scrollbar_light'],
                                                            colors['scrollbar_dark']
                                                        ])
            combobox.set(set_value)
            return combobox, scrollable_dropdown
        else:
            combobox.set(set_value)
            return combobox


    # MENSAGENS DE ERRO
    def show_null_name_error(self, new_window):
        msg = CTkMessagebox.CTkMessagebox(self,
                                          icon="warning",
                                          title="Nome selecionado",
                                          message="Por favor, selecione um nome da lista!",
                                          border_color="#FFA903",
                                          fade_in_duration=50,
                                          corner_radius=1,
                                          option_1="OK",
                                          fg_color=[colors['background_first_light'],
                                                    colors['background_first_dark']],
                                          button_color=[colors["button_submit_light"],
                                                        colors["button_submit_dark"]],
                                          button_hover_color=[colors["button_submit_hover_light"],
                                                              colors["button_submit_hover_dark"]])
        response = msg.get()
        if response == "OK":
            new_window.grab_set()
        else:
            new_window.grab_release()

    def show_success_message(self):
        CTkMessagebox.CTkMessagebox(self,
                                    icon="check",
                                    title="Relatório gerado",
                                    message="Relatório gerado com sucesso!",
                                    border_color="#6b50a1",
                                    fade_in_duration=50,
                                    corner_radius=1,
                                    fg_color=[colors['background_first_light'],
                                              colors['background_first_dark']],
                                    button_color=[colors["button_submit_light"],
                                                  colors["button_submit_dark"]],
                                    button_hover_color=[colors["button_submit_hover_light"],
                                                        colors["button_submit_hover_dark"]])

    def show_empty_field_error(self, value):
        CTkMessagebox.CTkMessagebox(self,
                                    icon="warning",
                                    title="Campo vazio",
                                    message=f"{value.upper()}\nESTÁ VAZIO!\nPor favor, preencha-o.",
                                    border_color="#FFA903",
                                    fade_in_duration=50,
                                    corner_radius=1,
                                    fg_color=[colors['background_first_light'],
                                              colors['background_first_dark']],
                                    button_color=[colors["button_submit_light"],
                                                  colors["button_submit_dark"]],
                                    button_hover_color=[colors["button_submit_hover_light"],
                                                        colors["button_submit_hover_dark"]])

    def show_county_not_found(self, value):
        CTkMessagebox.CTkMessagebox(self,
                                    icon="warning",
                                    title="Municipio não encontrado",
                                    message=f"O município está incorreto!\nEscolha na lista novamente.",
                                    border_color="#FFA903",
                                    fade_in_duration=50,
                                    corner_radius=1,
                                    fg_color=[colors['background_first_light'],
                                              colors['background_first_dark']],
                                    button_color=[colors["button_submit_light"],
                                                  colors["button_submit_dark"]],
                                    button_hover_color=[colors["button_submit_hover_light"],
                                                        colors["button_submit_hover_dark"]])

    def show_invalid_cpf(self):
        CTkMessagebox.CTkMessagebox(self,
                                    icon="warning",
                                    title="CPF inválido",
                                    message="CPF inválido!\nPor favor, digite um CPF válido.",
                                    border_color="#FFA903",
                                    fade_in_duration=50,
                                    corner_radius=1,
                                    fg_color=[colors['background_first_light'],
                                              colors['background_first_dark']],
                                    button_color=[colors["button_submit_light"],
                                                  colors["button_submit_dark"]],
                                    button_hover_color=[colors["button_submit_hover_light"],
                                                        colors["button_submit_hover_dark"]])

    def unr_names_not_found(self):
        CTkMessagebox.CTkMessagebox(self,
                                    icon="warning",
                                    title="Candidato não encontrado",
                                    message="Nenhum candidato encontrado!\n"
                                            "Verifique se o NOME ou o CPF estão corretos e tente novamente.",
                                    border_color="#FFA903",
                                    fade_in_duration=50,
                                    corner_radius=1,
                                    fg_color=[colors['background_first_light'],
                                              colors['background_first_dark']],
                                    button_color=[colors["button_submit_light"],
                                                  colors["button_submit_dark"]],
                                    button_hover_color=[colors["button_submit_hover_light"],
                                                        colors["button_submit_hover_dark"]])

    # Body da aplicação
    def system_app(self):
        # Frame para inserir o titulo/logo da aplicação
        frame = ctk.CTkFrame(self,
                             width=900,
                             height=60,
                             corner_radius=0)
        frame.place(x=0, y=10)

        # Titulo da aplicação
        title = ctk.CTkLabel(frame,
                             text="Eleição Transparente",
                             font=("Inter bold", 24),
                             text_color=[colors['title_logo_light'], colors['title_logo_dark']],
                             )
        title.place(relx=0.5, rely=0.5, anchor=CENTER)

        # Informando ao usuário que ele deve preencher todos os campos
        span = ctk.CTkLabel(self,
                            text="Por favor, preencha todos os campos do formulário!",
                            font=("Inter medium", 16),
                            text_color=["#000", "#fff"]
                            )
        span.place(x=50, y=70)

        # Função para selecionar caminho dos arquivos de acordo com a eleição escolhida
        def election_file_path(selected_election):
            # Dicionário com os caminhos de entrada dos arquivos na ordem: VOTOS POR ZONA - COLEGIOS
            eleicao_2020 = {
                'zone_votes': './src/files/2020/votacao_2020_RJ.csv',
                'schools': './src/files/2020/colegios_2020.csv'
            }
            eleicao_2016 = {
                'zone_votes': './src/files/2016/votacao_2016_RJ.csv',
                'schools': './src/files/2016/colegios_2016.csv'
            }
            eleicao_2012 = {
                'zone_votes': './src/files/2012/votacao_2012_RJ.csv',
                'schools': './src/files/2012/colegios_2012.csv'
            }

            election_file = {
                "2020": eleicao_2020,
                "2016": eleicao_2016,
                "2012": eleicao_2012
            }

            while True:
                if selected_election in election_file:
                    election = election_file[selected_election]
                    zone_votes = election['zone_votes']
                    schools = election['schools']
                    print(zone_votes, schools)
                    return zone_votes, schools
                else:
                    print(selected_election)
                    print("Eleição inválido, tente novamente.")
                    break

        # Função para pesquisar os nomes de urna do candidato
        def seek_urn_names(cpf=None, name=None):
            # Arquivos CSV das eleições
            files = [
                './src/files/2020/consulta_candidato_2020.csv',
                './src/files/2016/consulta_candidato_2016.csv',
                './src/files/2012/consulta_candidato_2012.csv'
            ]

            # Listas para armazenar os nomes encontrados
            urn_names = []      # Nomes de urna
            full_names = []     # Nome completo

            # Percorre cada um dos arquivos CSV
            for file in files:
                df = pd.read_csv(file, encoding='ISO-8859-1', sep=';', quotechar='"')

                # Renomear as colunas do DataFrame
                df = df.rename(columns={'NM_URNA_CANDIDATO': 'NOME_URNA',
                                        'NM_CANDIDATO': 'NOME_COMPLETO'})

                # Remove os acentos dos nomes de urna e nomes completos
                df['NOME_URNA'] = df['NOME_URNA'].apply(lambda x: unidecode(x))
                df['NOME_COMPLETO'] = df['NOME_COMPLETO'].apply(lambda x: unidecode(x))

                # Adiciona zeros a esquerda no CPF que tiver menos de onze numeros
                df['NR_CPF_CANDIDATO'] = df['NR_CPF_CANDIDATO'].astype(str).str.zfill(11)

                # Busca o nome de urna pelo CPF ou pelo nome do candidato
                if cpf is not None:
                    urn_name_array = df[df['NR_CPF_CANDIDATO'] == cpf]['NOME_URNA'].values
                    full_name_array = df[df['NR_CPF_CANDIDATO'] == cpf]['NOME_COMPLETO'].values
                else:
                    urn_name_array = df[df['NOME_COMPLETO'] == name]['NOME_URNA'].values
                    full_name_array = df[df['NOME_COMPLETO'] == name]['NOME_COMPLETO'].values

                if urn_name_array.size > 0:
                    urn_name = urn_name_array[0]
                else:
                    urn_name = None

                if full_name_array.size > 0:
                    full_name = full_name_array[0]
                else:
                    full_name = None

                # Adiciona o NOME_URNA(urn_name) e NOME_COMPLETO(full_name) encontrados às listas
                urn_names.append(urn_name)

                # O nome completo é adicionado à lista para que o usuário possa ter mais liberdade em
                # decidir qual nome ele quer ver no relatório
                urn_names.append(full_name)

            # Remove as duplicatas dos nomes de urna para ao fim não retornar nomes repetidos ao usuário
            urn_names = list(set(urn_names))

            # Filtra os resultados com valor None e remove-os da lista, isso acontece quando o candidato não
            # participou de alguma eleição específica ou quando o CPF ou nome do candidato não é encontrado
            urn_names = [name for name in urn_names if name is not None]

            # Ordena os nomes de urna em ordem alfabética
            urn_names.sort()
            return urn_names, full_names

        # Chama a função buscar_nomes_urna
        def interacao_busca(cpf_name_candidate, search_type, office, county, output_file_name, zone_votes, schools):
            while True:
                try:
                    # Busca por CPF
                    if search_type == "CPF":
                        print("Busca por CPF")
                        # cpf_name_candidate = int(cpf_name_candidate)
                        urn_names, full_names = seek_urn_names(cpf=cpf_name_candidate)
                        break
                    # Busca por nome do candidato
                    else:
                        # print("Busca por nome do candidato")
                        # print('parei por aqui')
                        urn_names, full_names = seek_urn_names(name=cpf_name_candidate)
                        # print(full_names)
                        # print(urn_names)
                        break
                except ValueError:
                    print("Erro CPF/NOME")

            while True:
                try:
                    if urn_names:
                        # print(urn_names)
                        show_urn_names(urn_names, office, county, output_file_name, zone_votes, schools)
                        return urn_names
                    else:
                        self.unr_names_not_found()
                        break
                except (ValueError, IndexError):
                    print("nome, tente novamente.")

        def get_selected_item(new_window, listbox, urn_names, office, county, output_file_name, zone_votes, schools):
            selected_name = listbox.get()
            if selected_name:
                # print(selected_name)
                new_window.withdraw()

                submit_urn_name(selected_name, urn_names, office, county, output_file_name, zone_votes, schools)
            else:
                self.show_null_name_error(new_window)

        def chama_get_selected_item(new_window, listbox,
                                    urn_names, office, county,
                                    output_file_name, zone_votes, schools):

            get_selected_item(new_window, listbox, urn_names, office, county, output_file_name, zone_votes, schools)
            new_window.grab_release()

        def cancel_selected_item(new_window):
            new_window.grab_release()
            new_window.withdraw()

        def do_nothing():
            pass

        def show_urn_names(urn_names, office, county, output_file_name, zone_votes, schools):
            # Cria uma nova janela
            new_window = MyCTkToplevel(self)
            new_window.title("Escolha o nome da urna")

            new_window.geometry("450x300")
            # Fetches the requested dimensions
            window_width = new_window.winfo_reqwidth()
            window_height = new_window.winfo_reqheight()
            new_window.configure(highlightbackground=colors['border_input_text_light'],
                                 highlightcolor=colors['border_input_text_light'],
                                 highlightthickness=5,)
            new_window.grab_set()
            new_window.protocol("WM_DELETE_WINDOW", do_nothing)
            new_window.resizable(False, False)

            # Get the top left coordinates of the parent window
            parent_x = self.winfo_rootx()
            parent_y = self.winfo_rooty()

            # Get the width and height of the parent window
            parent_width = self.winfo_width()
            parent_height = self.winfo_height()

            # Calculate position
            position_right = int(parent_x + parent_width/2 - window_width/2)
            position_down = int(parent_y + parent_height/2 - window_height/2)

            # Positions the window
            new_window.geometry("+{}+{}".format(position_right, position_down))

            lb_title_urn_name = ctk.CTkLabel(new_window,
                                             text="Escolha o nome para seu relatório:".upper(),
                                             font=("Inter medium", 14),
                                             text_color=["#000", "#fff"])
            lb_title_urn_name.place(relx=0.5, rely=0.2, anchor=CENTER)

            # Cria um listbox
            listbox = CTkListbox(new_window,
                                 text_color=["#000", "#fff"],
                                 border_width=2,
                                 justify="center",
                                 font=("Inter regular", 14),
                                 width=360,
                                 bg_color=[
                                     colors['background_first_light'],
                                     colors['background_first_dark']
                                 ],
                                 fg_color=[
                                     colors['background_first_light'],
                                     colors['background_first_dark']
                                 ],
                                 border_color=[
                                     colors['border_input_text_light'],
                                     colors['border_input_text_dark']
                                 ],
                                 scrollbar_fg_color=[
                                     colors['background_first_light'],
                                     colors['background_first_dark']
                                 ],
                                 scrollbar_button_color=[
                                     colors['background_first_light'],
                                     colors['background_first_dark']
                                 ],
                                 scrollbar_button_hover_color=[
                                     colors['background_first_light'],
                                     colors['background_first_dark']
                                 ])
            listbox.place(relx=0.5, rely=0.5, anchor=CENTER)

            # Adiciona os nomes de urna ao listbox
            for urn_name in urn_names:
                listbox.insert(END, urn_name)

            # Cria um botão para obter o nome de urna selecionado
            btn_selected_name = ctk.CTkButton(new_window, text="Selecionar".upper(),
                                              fg_color=[
                                                  colors["button_submit_light"],
                                                  colors["button_submit_dark"]
                                              ],
                                              hover_color=[
                                                  colors["button_submit_hover_light"],
                                                  colors["button_submit_hover_dark"]
                                              ],
                                              command=lambda: chama_get_selected_item(
                                                  new_window,
                                                  listbox,
                                                  urn_names,
                                                  office,
                                                  county,
                                                  output_file_name,
                                                  zone_votes,
                                                  schools
                                              ))
            btn_selected_name.place(x=280, y=280, anchor=CENTER)

            btn_cancel_name = ctk.CTkButton(new_window,
                                            text="Cencelar".upper(),
                                            fg_color=colors['button_clear'],
                                            command=lambda: cancel_selected_item(new_window))
            btn_cancel_name.place(x=120, y=280, anchor=CENTER)

        # Colhe os dados do formulário e gera o relatório
        def submit():
            # Verifica se o tipo de busca é por CPF ou por Nome
            if self.search_type_combobox.get() == "CPF":
                cpf_name_value = self.cpf_var.get()
                cpf_name_candidate = cpf_name_value.replace('.', '').replace('-', '')
            else:
                cpf_name_value = self.name_var.get()
                cpf_name_value = cpf_name_value.strip()
                cpf_name_candidate = re.sub(' +', ' ', cpf_name_value)

            search_type = self.search_type_combobox.get()
            selected_election = election_combobox.get()
            office = office_combobox.get()

            county_value = self.county_combobox.get()
            county_value = ''.join(c for c in county_value if c.isalpha() or c.isspace())
            county_value = county_value.strip()
            county_value = re.sub(' +', ' ', county_value)
            county = unidecode(county_value).upper()

            output_value = self.output_file_name_var.get()
            output_value = output_value.replace('_', ' ')
            output_value = output_value.strip()
            output_value = re.sub(' +', ' ', output_value)
            output_file_name = output_value.replace(' ', '_').lower()

            # Verifica se os campos estão vazios
            fields_inputs = {
                "output_file_name": [output_file_name, lb_output_file_name.cget("text")],
                "cpf_name": [cpf_name_candidate, lb_cpf_name.cget("text")],
                "county": [county, lb_county.cget("text")],
            }
            if any(value[0] == "" for value in fields_inputs.values()):
                for field, value in fields_inputs.items():
                    if value[0] == "":
                        print(f"O campo {value[1]} está vazio! {value[0]}")
                        self.show_empty_field_error(value[1])
                        break
            else:
                if fields_inputs["county"][0] not in county_list:
                    print(f"O valor {fields_inputs['county'][0]} não está na lista de municípios!")
                    self.show_county_not_found(fields_inputs["county"][0])

                elif len(cpf_name_candidate) < 11 and search_type == "CPF":
                    print(f"CPF inválido!\nPor favor, digite um CPF válido.")
                    self.show_invalid_cpf()
                else:
                    zone_votes, schools = election_file_path(selected_election)
                    interacao_busca(
                        cpf_name_candidate, search_type,
                        office, county, output_file_name,
                        zone_votes, schools
                    )
                    return office, county, output_file_name, zone_votes, schools

        def submit_urn_name(selected_name, urn_names, office, county, output_file_name, zone_votes, schools):
            # Dicionário com os caminhos de saida dos arquivos na ordem: RELATORIO - RANKING
            result_nbhd = f'./result/{output_file_name}_bairro.csv'
            result_ranking_nbhd = f'./result/{output_file_name}_ranking_bairro.csv'
            result_ranking_nbhd_graph = f'./result/{output_file_name}_ranking_grafico.png'

            self.btn_submit.place_forget()
            progressbar = ctk.CTkProgressBar(self,
                                             width=180,
                                             height=15,
                                             orientation="horizontal",
                                             progress_color=[colors["border_input_text_light"],
                                                             colors["border_input_text_dark"]],
                                             fg_color="#D9D9D9",
                                             mode="indeterminate")
            progressbar.place(relx=0.5, y=400, anchor=CENTER)
            progressbar.start()

            def monitor_thread(thread_to_check):
                if thread_to_check.is_alive():
                    app.after(100, monitor_thread, thread_to_check)
                else:
                    # Mostra uma mensagem de sucesso
                    self.show_success_message()
                    progressbar.stop()
                    progressbar.destroy()
                    self.btn_submit.place(relx=0.5, y=400, anchor=CENTER)

            def generate_reports():
                # print("sucesso")
                gerar_rel_bairro(zone_votes,
                                 schools,
                                 county,
                                 selected_name,
                                 urn_names,
                                 result_nbhd)

                gerar_rel_rank_bairro(zone_votes,
                                      schools,
                                      county,
                                      selected_name,
                                      urn_names,
                                      office,
                                      result_ranking_nbhd,
                                      result_ranking_nbhd_graph)

            background_thread = threading.Thread(target=generate_reports)
            background_thread.start()
            monitor_thread(background_thread)    # Check the thread every 100ms

        # Limpa os campos do formulário
        def clear():
            # Trata dos erros do county_combobox_dropdown
            try:
                # Check if the dropdown exists before trying to destroy it
                if self.county_combobox_dropdown:
                    # Call live_update before destroying the dropdown
                    self.county_combobox_dropdown.live_update("")
                    # Unbind the events
                    self.county_combobox_dropdown.attach.unbind('<Double-Button-1>')
                    self.county_combobox_dropdown.attach.winfo_toplevel().unbind('<Triple-Button-1>')
                    self.county_combobox_dropdown.attach.winfo_toplevel().unbind('<Configure>')
                    # Cancel any pending after calls
                    # if hasattr(self.county_combobox_dropdown, 'after_id'):
                    #     self.county_combobox_dropdown.after_cancel(self.county_combobox_dropdown.after_id)
                    # Destroy the dropdown
                    self.county_combobox_dropdown.destroy()
                    self.county_combobox_dropdown = None
            except Exception as e:
                print(f"Failed to destroy dropdown: {e}")
                print(f"Exception type: {type(e)}")

            election_combobox.set("2020")
            office_combobox.set("PREFEITO")
            self.county_combobox, _ = self.create_ctk_combobox("normal", "left", None, True,
                                                               300, 35, county_list, "ESCOLHA O MUNICÍPIO", True)
            self.county_combobox.place(x=50, y=260)
            # self.county_combobox_dropdown.set(county_list)
            self.cpf_var.set('')  # clear the cpf_entry
            self.cpf_entry.configure(state="disabled",
                                     border_color="#fff")

            self.search_type_combobox.set("NOME")
            self.name_var.set('')  # clear the name_entry
            self.name_entry.delete(0, 'end')

            self.output_file_name_var.set('')  # clear the output_file_name_entry
            self.output_file_name_entry.delete(0, 'end')

            # validate_cmd = self.register(lambda value: value == "" or value.isalpha())
            # Altera o texto do label
            lb_cpf_name.configure(text="Nome completo do candidato:")

            self.search_type_combobox.set("NOME")
            self.name_entry.configure(state="normal",
                                      validate="key",
                                      textvariable=self.name_var,
                                      validatecommand=(self.register(self.validate_entry_name), "%P"))

        # Entry variables
        # Variable CPF
        self.cpf_var = StringVar()
        self.cpf_var.trace('w', self.format_cpf)

        # Variable Name
        self.name_var = StringVar()
        self.name_var.trace('w', self.format_entry_name)

        # Variable Output File Name
        self.output_file_name_var = StringVar()
        self.output_file_name_var.trace('w', self.format_entry_output)

        # Criação dos campos de entrada
        def create_ctk_entry(parent, validate_cmd, text_variable, state, width):
            return ctk.CTkEntry(self,
                                validatecommand=validate_cmd,
                                font=("Inter", 16),
                                textvariable=text_variable,
                                fg_color=colors['input_text'],
                                state=state,
                                validate="key",
                                width=width,
                                height=35,
                                corner_radius=8,
                                border_width=2,
                                border_color=[
                                    colors['border_input_text_light'],
                                    colors['border_input_text_dark']
                                ])

        # Input CPF
        self.cpf_entry = create_ctk_entry(self,
                                          (self.register(self.validate_entry_cpf), "%P"),
                                          self.cpf_var, "disabled", 230)

        # Input Name
        self.name_entry = create_ctk_entry(self,
                                           (self.register(self.validate_entry_name), "%P"),
                                           self.name_var, "normal", 350)


        # Input Output File Name
        self.output_file_name_entry = create_ctk_entry(self,
                                                       (self.register(self.validate_entry_output), "%P"),
                                                       self.output_file_name_var, "normal", 350)

        # Alternancia entre os campos CPF e NOME
        def toggle_entry_fields(event):
            # Pega o valor selecionado no search_type_combobox
            selected_option = self.search_type_combobox.get()

            if selected_option == "NOME":
                # Altera a validação do Entry para permitir apenas letras
                # Validação do Nome
                # validate_cmd = self.register(lambda value: value == "" or value.isalpha())

                self.name_entry.configure(validatecommand=(self.register(self.validate_entry_name), "%P"),
                                          textvariable=self.name_var,
                                          validate="key",
                                          state="normal")
                # Limpa o campo
                self.name_entry.delete(0, 'end')

                # Altera o texto da label
                lb_cpf_name.configure(text="Nome completo do candidato:")

            elif selected_option == "CPF":
                # Altera a validação do Entry para permitir apenas números
                validate_cmd_cpf_toggle = self.register(lambda value: value == "" or value.isdigit())
                self.name_entry.configure(validatecommand=(validate_cmd_cpf_toggle, "%P"),
                                          textvariable=self.cpf_var,
                                          validate="key",
                                          state="normal")
                # Limpa o campo
                self.name_entry.delete(0, 'end')

                # Altera o texto do label
                lb_cpf_name.configure(text="CPF do candidato:")




        # Election combobox
        election_combobox, _ = self.create_ctk_combobox("readonly", "center", None, False,
                                                        130, 35, ["2020", "2016", "2012"], "2020", True)

        # Office ComboBox
        office_combobox, _ = self.create_ctk_combobox("readonly", "center", None, False,
                                                      130, 35, ["PREFEITO", "VEREADOR"], "PREFEITO", True)

        self.county_combobox, self.county_combobox_dropdown = self.create_ctk_combobox("normal", "left", None, True,
                                                                                       300, 35, county_list,
                                                                                       "ESCOLHA O MUNICÍPIO", True)
        # county_combobox.pack(pady=20)

        # ComboBox CPF/NOME
        self.search_type_combobox = self.create_ctk_combobox("readonly", "center", toggle_entry_fields, False,
                                                    130, 35, ["NOME", "CPF"], "NOME", False)

        def create_ctk_label(parent, text):
            return ctk.CTkLabel(self,
                                text=text,
                                font=("Inter medium", 16),
                                text_color=[colors["label_light"], colors['label_dark']])

        # Labels dos campos
        # Label Election
        lb_election = create_ctk_label(self, "Ano da Eleição:")

        # Label Search Type
        lb_search_type = create_ctk_label(self, "Tipo de busca:")

        # Label Name
        lb_cpf_name = create_ctk_label(self, "Nome completo do candidato:")

        # Label Output File Name
        lb_output_file_name = create_ctk_label(self, "Nome do arquivo de saída:")

        # Label Município
        lb_county = create_ctk_label(self, "Município em que houve a eleição:")

        # Label Office
        lb_office = create_ctk_label(self, "Cargo concorrido:")

        # Label Button Submit
        self.btn_submit = ctk.CTkButton(self,
                                        text="Gerar relatório".upper(),
                                        font=("Inter medium", 16),
                                        command=submit,
                                        width=180,
                                        height=45,
                                        text_color=["#fff", "#fff"],
                                        fg_color=[
                                            colors["button_submit_light"],
                                            colors["button_submit_dark"]
                                        ],
                                        hover_color=[
                                            colors["button_submit_hover_light"],
                                            colors["button_submit_hover_dark"]
                                        ])
        self.btn_submit.place(relx=0.5, y=400, anchor=CENTER)

        # Label Button Clear
        btn_clear = ctk.CTkButton(self,
                                  text="Limpar os campos".upper(),
                                  font=("Inter medium", 16),
                                  width=180,
                                  height=45,
                                  command=clear,
                                  fg_color=colors["button_clear"],
                                  hover_color=colors["button_clear_hover"],
                                  bg_color="transparent",
                                  text_color=["#fff", "#fff"]
                                  )
        btn_clear.place(relx=0.5, y=450, anchor=CENTER)

        # Posicionando os elementos na janela
        # Election
        lb_election.place(x=50, y=130)
        election_combobox.place(x=50, y=160)

        # Search Type
        lb_search_type.place(x=610, y=130)
        self.search_type_combobox.place(x=610, y=160)

        # County
        lb_county.place(x=50, y=230)
        self.county_combobox.place(x=50, y=260)

        # CPF/Name
        lb_cpf_name.place(x=500, y=200)
        self.name_entry.place(x=500, y=230)

        # Office
        lb_office.place(x=220, y=130)
        office_combobox.place(x=220, y=160)

        # Output File Name
        lb_output_file_name.place(x=500, y=280)
        self.output_file_name_entry.place(x=500, y=310)

    @staticmethod
    def open_github(event):
        webbrowser.open("https://github.com/hugoromerito")

    @staticmethod
    def open_linkedin(event):
        webbrowser.open("https://www.linkedin.com/in/hugoromerito/")

    @staticmethod
    def open_insta(event):
        webbrowser.open("https://www.instagram.com/hugo_sqz/")

    def footer(self):
        # Caminho dos icons
        icon_git = ctk.CTkImage(light_image=Image.open("./src/images/github_light.png"),
                                dark_image=Image.open("./src/images/github_dark.png"),
                                size=(30, 30))

        icon_linkedin = ctk.CTkImage(light_image=Image.open("./src/images/linkedin_light.png"),
                                     dark_image=Image.open("./src/images/linkedin_dark.png"),
                                     size=(30, 30))

        icon_insta = ctk.CTkImage(light_image=Image.open("./src/images/insta_light.png"),
                                  dark_image=Image.open("./src/images/insta_dark.png"),
                                  size=(30, 30))

        # Criando o label com os icons
        lb_icon_github = ctk.CTkLabel(self,
                                      image=icon_git,
                                      cursor="hand2",
                                      text="")

        lb_icon_linkedin = ctk.CTkLabel(self,
                                        image=icon_linkedin,
                                        cursor="hand2",
                                        text="")

        lb_icon_insta = ctk.CTkLabel(self,
                                     image=icon_insta,
                                     cursor="hand2",
                                     text="")

        # Posicionando os icons
        lb_icon_github.place(x=820, y=370)
        lb_icon_linkedin.place(x=820, y=405)
        lb_icon_insta.place(x=820, y=440)

        # Link dos icons
        lb_icon_github.bind("<Button-1>", self.open_github)
        lb_icon_linkedin.bind("<Button-1>", self.open_linkedin)
        lb_icon_insta.bind("<Button-1>", self.open_insta)

        # Label Create by
        lb_create_by = ctk.CTkLabel(self,
                                    text="By: Hugo Queiroz",
                                    font=("Inter medium", 14),
                                    fg_color="transparent",
                                    text_color=[colors["border_input_text_light"], colors['border_input_text_dark']])
        # Footer Create by
        lb_create_by.place(x=733, y=470)

    # Theme function
    @staticmethod
    def change_apm(new_apm):
        ctk.set_appearance_mode(new_apm)


if __name__ == '__main__':
    app = App()
    app.mainloop()
