import pandas as pd
import dash
from dash import dash_table
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash import dcc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import base64
import io
import dash_auth
from optaloA3 import SquadAllocatorLP
import plotly.express as px
from dash_bootstrap_templates import load_figure_template
load_figure_template(["cyborg", "darkly"])

# Inicializa o DataFrame vazio
df_alocacoes = pd.DataFrame(columns=['PROJETO_ID', 'CARGO', 'SETOR', 'CLASSE', 'QUANTIDADE', 'HORAS', 'PROJETOS', 'CUSTO'])
csv_data = pd.DataFrame()

# Função para realizar as análises no DataFrame carregado
import pandas as pd

def analisar_csv(df, df_alocacoes):
    """
    Realiza análises no DataFrame carregado a partir de um arquivo CSV.

    Parameters:
    - df (pd.DataFrame): O DataFrame a ser analisado.
    - df_alocacoes (pd.DataFrame): O DataFrame de referência com as informações de alocamento.

    Returns:
    - pd.DataFrame or str: Retorna o DataFrame analisado se todas as verificações passarem. Retorna uma mensagem de erro se alguma verificação falhar.
    """
    if set(df.columns) != {'PROJETO_ID', 'CARGO', 'SETOR', 'CLASSE', 'QUANTIDADE', 'HORAS', 'PROJETOS', 'CUSTO'}:
        return "O arquivo CSV deve conter as colunas: PROJETO_ID, CARGO, SETOR, CLASSE, QUANTIDADE, HORAS, PROJETOS, CUSTO."

    if (df[['QUANTIDADE', 'HORAS', 'PROJETOS', 'CUSTO']] < 0).any().any():
        return "O arquivo CSV não pode conter números negativos."

    cargos_base = set(df_alocacoes['CARGO'].unique())
    setores_base = set(df_alocacoes['SETOR'].unique())
    classes_base = set(df_alocacoes['CLASSE'].unique())

    cargos_csv = set(df['CARGO'].unique())
    setores_csv = set(df['SETOR'].unique())
    classes_csv = set(df['CLASSE'].unique())

    if not cargos_csv.issubset(cargos_base):
        return "Valores inválidos encontrados na coluna CARGO do arquivo CSV."

    if not setores_csv.issubset(setores_base):
        return "Valores inválidos encontrados na coluna SETOR do arquivo CSV."

    if not classes_csv.issubset(classes_base):
        return "Valores inválidos encontrados na coluna CLASSE do arquivo CSV."

    return df

def gerar_visao_macro():
    """
    Carrega o arquivo "alocamento_colaboradores_projetos.csv" e gera a visão macro.

    Returns:
    - pd.DataFrame: Retorna o DataFrame da visão macro.
    """
    alocamentos = pd.read_csv("data_input/alocamento_colaboradores_projetos.csv")

    visao_macro = alocamentos.groupby('col_matricula').agg({
        'col_custo': 'first',
        'col_cargo': 'first',
        'col_setor': 'first',
        'col_classe': 'first',
        'pro_number': 'nunique',
        'horas_alocadas': 'sum'
    }).reset_index()

    visao_macro.columns = ['col_nome', 'col_custo_hora', 'col_cargo', 'col_setor', 'col_classe',
                            'col_number_proj', 'col_hora_alocada']
    return visao_macro

VALID_USERNAME_PASSWORD_PAIRS = {
    'admin': 'admin'
}

# Configurando o aplicativo Dash
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY],
                suppress_callback_exceptions=True)
auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

df_graph = gerar_visao_macro().groupby(['col_cargo', 'col_classe']).size().reset_index(name='count')
df_graph.columns = ['Cargo','Classe','Quantidade']

# Estilo global do aplicativo
app.layout = html.Div([
    
    html.Img(
        src="https://a3data.com.br/wp-content/themes/a3data/img/logo_original.png",
        style={'width': '150px', 'height': 'auto', 'position': 'absolute', 'top': '20px', 'left': '20px'}
    ),

    html.H1('Otimização da Alocação', style={'textAlign': 'center', 'font-family': 'Verdana','margin-bottom': '20px','top-bottom': '20px', 'font-weight': 'bold'}),

    # Título da tabela
    html.Div([
        html.H2("Tabela de Distribuição de Colaboradores", style={'padding': '10px', 'margin-bottom': '10px', 'textAlign': 'center','font-family': 'Verdana', 'font-weight': 'bold','color':'white','fontSize': '25px'}),
        
        # Tabela 1: Distribuição de Colaboradores
        html.Div(style={'background-color': 'black', 'color': 'white'}, children=[
            dcc.Graph(
                id='bar-chart',
                figure=px.bar(df_graph,x='Cargo', y='Quantidade', color='Classe', barmode='group', labels={'Cargo': 'Cargo', 'Quantidade': 'Quantidade'}, template='darkly'),
                style={'background-color': 'black', 'color': 'white','font-size': '24px','font-family': 'Verdana'}
            )
        ]),

        html.H2("Tabela de Mapa de Calor dos Colaboradores", style={'padding': '10px', 'margin-bottom': '10px', 'textAlign': 'center','font-family': 'Verdana', 'font-weight': 'bold','color':'white','fontSize': '25px'}),

        # Dropdown para selecionar a coluna do mapa de calor
        dcc.Dropdown(
            id='heatmap-column',
            options=[
                {'label': 'Número de Projetos', 'value': 'col_number_proj'},
                {'label': 'Horas Alocadas', 'value': 'col_hora_alocada'},
                {'label': 'Custo', 'value': 'col_custo_hora'}
            ],
            value='col_hora_alocada',  # Valor padrão
            style={
                'width': '100%',
                'margin': '0 auto',
                'textAlign': 'center',
                'font-family': 'Verdana',
                'font-weight': 'bold',
                'fontSize': '12px',
                'color': 'black',  # Define a cor do texto para branco
                'background-color': '#f5009cff',  # Define a cor de fundo no mesmo estilo que o cabeçalho
                'border': 'none', # Remove a borda
            },
        ),
    ]),
    
    # Tabela 2: Mapa de Calor
    dash_table.DataTable(
        id='table2',
        columns=[
            {"name": "Matricula", "id": "col_nome"},
            {"name": "Cargo", "id": "col_cargo"},
            {"name": "Setor", "id": "col_setor"},
            {"name": "Classe", "id": "col_classe"},
            {"name": "Número de Projetos", "id": "col_number_proj"},
            {"name": "Horas Alocadas", "id": "col_hora_alocada"},
            {"name": "Custo", "id": "col_custo_hora"}
        ],
        style_as_list_view=True,
        style_header={'backgroundColor': '#f5009cff', 'color': '#ffdd19', 'font-weight': 'bold', 'textAlign': 'center', 'fontSize': '20px', 'font-family': 'Verdana'},
        style_table={'height': '400px', 'overflowY': 'auto', 'marginTop': '20px', 'marginBottom': '20px'},
        filter_action="native",
        style_filter={'backgroundColor': '#061d74',
        'color': 'white',
        'fontWeight': 'bold'}
    ),

    html.H3('Construa uma Tabela de Alocação para um Novo Projeto', style={'padding': '10px', 'margin-bottom': '10px', 'textAlign': 'center','font-family': 'Verdana', 'font-weight': 'bold','color':'white','fontSize': '25px'}),
    
    # Dropdown para selecionar o cargo
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Arraste e solte ou selecione arquivo CSV com os dados de alocação',
            html.A('')
        ]),
        style={
            'width': '50%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px auto',
            'marginBottom': '20px',
            'marginTop': '20px'
        },
        multiple=False
    ),

    html.Div([
        html.Div([
            dcc.Dropdown(
                id='cargo-dropdown',
                options=[{'label': cargo, 'value': cargo} for cargo in gerar_visao_macro()['col_cargo'].unique()],
                value=None,
                placeholder='Cargo',
                style={
                    'marginTop': '20px', 
                    'marginBottom': '20px',
                    'width': '100%',
                    'margin': '0 auto',
                    'textAlign': 'center',
                    'font-family': 'Verdana',
                    'font-weight': 'bold',
                    'fontSize': '12px',
                    'color': 'black',  # Define a cor do texto para branco
                    'background-color': '#f5009cff',  # Define a cor de fundo no mesmo estilo que o cabeçalho
                    'border': 'none'  # Remove a borda
                },
            ),
            dcc.Dropdown(
                id='setor-dropdown',
                options=[{'label': setor, 'value': setor} for setor in gerar_visao_macro()['col_setor'].unique()],
                value=None,
                placeholder='Setor',
                style={
                    'marginTop': '20px', 
                    'marginBottom': '20px',
                    'width': '100%',
                    'margin': '0 auto',
                    'textAlign': 'center',
                    'font-family': 'Verdana',
                    'font-weight': 'bold',
                    'fontSize': '12px',
                    'color': 'black',  # Define a cor do texto para branco
                    'background-color': '#f5009cff',  # Define a cor de fundo no mesmo estilo que o cabeçalho
                    'border': 'none'  # Remove a borda
                },
            ),
            dcc.Dropdown(
                id='classe-dropdown',
                options=[{'label': classe, 'value': classe} for classe in gerar_visao_macro()['col_classe'].unique()],
                value=None,
                placeholder='Classe',
                style={
                    'marginTop': '20px', 
                    'marginBottom': '20px',
                    'width': '100%',
                    'margin': '0 auto',
                    'textAlign': 'center',
                    'font-family': 'Verdana',
                    'font-weight': 'bold',
                    'fontSize': '12px',
                    'color': 'black',  # Define a cor do texto para branco
                    'background-color': '#f5009cff',  # Define a cor de fundo no mesmo estilo que o cabeçalho
                    'border': 'none'  # Remove a borda
                },
            ),
        ],
        style={'text-align': 'center',                    
               'marginTop': '20px', 
                'marginBottom': '20px'}  # Centraliza os dropdowns na div
        ),
    ]),

    html.Div([
        dcc.Input(
            id='horas-input',
            type='number',
            placeholder='Horas Alocadas',
            style={'margin-right': '10px','font-family': 'Verdana','text-align': 'center'},
            min=0  # Valor mínimo deve ser maior ou igual a 0
        ),
        dcc.Input(
            id='projetos-input',
            type='number',
            placeholder='Número de Projetos',
            style={'margin-right': '10px','font-family': 'Verdana','text-align': 'center'},
            min=0  # Valor mínimo deve ser maior ou igual a 0
        ),
        dcc.Input(
            id='custo-input',
            type='number',
            placeholder='Custo Máximo',
            style={'margin-right': '10px','font-family': 'Verdana','text-align': 'center'},
            min=0  # Valor mínimo deve ser maior ou igual a 0
        ),

        dcc.Input(
            id='quantidade-col-input',
            type='number',
            placeholder='Quantidade Colaboradores',
            style={'margin-right': '10px','font-family': 'Verdana','text-align': 'center'},
            min=0  # Valor mínimo deve ser maior ou igual a 0
        ),

        dcc.Input(
            id='nome-projeto-input',
            type='text',
            placeholder='Nome Projeto',
            style={'margin-right': '10px','font-family': 'Verdana','text-align': 'center'}
        ),


        html.Button(
            'Adicionar',
            id='add-allocation-button',
            style={
                'margin-top': '10px',
                'margin-left': 'auto',
                'margin-right': 'auto',
                'display': 'block', 
                'width': '30%',
                'text-align': 'center',
                'backgroundColor': '#f5009cff',
                'color': '#ffdd19',
                'border': 'none',
                'font-weight': 'bold',
                'font-family': 'Verdana',
                'padding': '10px 20px',
                'margin': '20px auto',
                'cursor': 'pointer',
            }
        )
    ], style={'text-align': 'center'}),

    html.Div([
        html.H3('Alocações de Projetos', style={'textAlign': 'center','font-family': 'Verdana', 'font-weight': 'bold','color':'white','fontSize': '25px'}),
        # Tabela para mostrar as alocações feitas
        dash_table.DataTable(
            id='allocation-table',
            columns=[
                {"name": "Nome Projeto", "id": "PROJETO_ID", 'editable': True},
                {"name": "Cargo", "id": "CARGO", 'editable': True},
                {"name": "Setor", "id": "SETOR", 'editable': True},
                {"name": "Classe", "id": "CLASSE", 'editable': True},
                {"name": "Horas Alocadas", "id": "HORAS", 'editable': True},
                {"name": "Custo", "id": "CUSTO", 'editable': True},
                {"name": "Quantidade", "id": "QUANTIDADE", 'editable': True},
            ],
            editable=True, 
            style_as_list_view=True,
            style_header={'backgroundColor': '#f5009cff', 'color': '#ffdd19', 'font-weight': 'bold', 'textAlign': 'center', 'fontSize': '20px', 'font-family': 'Verdana'},
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': 'rgb(50, 50, 50)',
                    'color': 'white',
                    'textAlign': 'center',
                    'font-family': 'Verdana'
                },
                {
                    'if': {'row_index': 'even'},
                    'backgroundColor': 'rgb(40, 40, 40)',
                    'color': 'white',
                    'textAlign': 'center',
                    'font-family': 'Verdana'
                },
            ],
            style_table={'height': '150px', 'overflowY': 'auto', 'marginTop': '20px', 'marginBottom': '20px'},
            data=[],
        ),
    ], style={'text-align': 'center'}),

    html.H2("Pesos do otimizador", style={'padding': '10px', 'margin-bottom': '10px', 'textAlign': 'center','font-family': 'Verdana', 'font-weight': 'bold','color':'white','fontSize': '25px'}),
    html.Div([
            # Peso de horas
            html.Div(
                [
                    html.H4('Peso de hora:', style={'font-family': 'Verdana', 'font-weight': 'bold', 'color': 'white', 'fontSize': '12px','text-align': 'center'}),
                    dcc.Input(
                        id='weight-hours-input',
                        type='number',
                        placeholder=1,
                        style={'margin-right': '10px', 'font-family': 'Verdana', 'text-align': 'center'},
                        min=0  # Valor mínimo deve ser maior ou igual a 0
                    )],
                    style={'display': 'inline-block', 'margin-right': '20px'}
                ),

            # Peso de projetos
            html.Div([
                    html.H4('Peso de projeto:', style={'font-family': 'Verdana', 'font-weight': 'bold', 'color': 'white', 'fontSize': '12px','text-align': 'center'}),
                    dcc.Input(
                        id='weight-projects-input',
                        type='number',
                        placeholder=1,
                        style={'margin-right': '10px', 'font-family': 'Verdana', 'text-align': 'center'},
                        min=0  # Valor mínimo deve ser maior ou igual a 0
                    )],
                    style={'display': 'inline-block', 'margin-right': '20px'}
                ),

            # Peso de custo
            html.Div(
                [
                    html.H4('Peso de custo:', style={'font-family': 'Verdana', 'font-weight': 'bold', 'color': 'white', 'fontSize': '12px','text-align': 'center'}),
                    dcc.Input(
                        id='weight-cost-input',
                        type='number',
                        placeholder=1,
                        style={'margin-right': '10px', 'font-family': 'Verdana', 'text-align': 'center'},
                        min=0  # Valor mínimo deve ser maior ou igual a 0
                    )],
                    style={'display': 'inline-block', 'margin-right': '20px'}
                ),

            # Número de Recomendações
            html.Div(
                [
                    html.H4('Número de Recomendações:', style={'font-family': 'Verdana', 'font-weight': 'bold', 'color': 'white', 'fontSize': '12px','text-align': 'center'}),
                    dcc.Input(
                        id='number-recommendations-input',
                        type='number',
                        placeholder=1,
                        style={'margin-right': '10px', 'font-family': 'Verdana', 'text-align': 'center'},
                        min=0  # Valor mínimo deve ser maior ou igual a 0
                    )],
                    style={'display': 'inline-block'}
                ),
            ],
            style={'text-align': 'center'}
        ),

    html.Div(
        [
            html.Button(
                'Otimizar Alocação',
                id='otimizar-button',
                disabled=True,
                style={
                    'width': '50%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'margin': '10px auto',
                    'marginBottom': '20px',
                    'marginTop': '20px',
                    'backgroundColor': '#f5009cff',
                    'color': '#ffdd19',
                    'border': 'none',
                    'font-weight': 'bold',
                    'font-family': 'Verdana',
                    'cursor': 'pointer',
                },
            ),
        ],
    style={'text-align': 'center'}),

    html.H2("Tabela de Recomendação de Alocação", style={'padding': '10px', 'margin-bottom': '10px', 'textAlign': 'center','font-family': 'Verdana', 'font-weight': 'bold','color':'white','fontSize': '25px'}),
    # Tabela para mostrar as recomendações da otimização
    dash_table.DataTable(
        id='recommendation-table',
        columns=[
            {"name": "Nome Projeto", "id": "PROJETO_ID"},
            {"name": "Matricula", "id": "col_nome"},
            {"name": "Cargo", "id": "col_cargo"},
            {"name": "Setor", "id": "col_setor"},
            {"name": "Classe", "id": "col_classe"},
            {"name": "Horas Alocadas", "id": "col_hora_alocada"},
            {"name": "Custo", "id": "col_custo_hora"},
            {"name": "Prioridade de Recomendação", "id": "RECOMENDACAO_PRIORIDADE"},
        ],
        data=[],
        style_as_list_view=True,
        style_header={'backgroundColor': '#f5009cff', 'color': '#ffdd19', 'font-weight': 'bold', 'textAlign': 'center', 'fontSize': '20px', 'font-family': 'Verdana'},
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(50, 50, 50)',
                'color': 'white',
                'textAlign': 'center',
                'font-family': 'Verdana'
            },
            {
                'if': {'row_index': 'even'},
                'backgroundColor': 'rgb(40, 40, 40)',
                'color': 'white',
                'textAlign': 'center',
                'font-family': 'Verdana'
            },
        ],
        style_table={'height': '400px', 'overflowY': 'auto', 'marginTop': '20px', 'marginBottom': '20px'},
        filter_action="native",
        style_filter={'backgroundColor': '#061d74',
        'color': 'white',
        'fontWeight': 'bold'
        }
    ),

    dcc.Store(id='csv-data-store', data=None),
    dcc.Store(id='df-alocacoes-store', data=None)

])

app.layout.template = "plotly_dark"
app.layout.paper_bgcolor = 'black'
app.layout.plot_bgcolor = 'black'
app.layout.font = {'color': 'white'}
app.layout.xaxis_title_font = {'size': 24}
app.layout.yaxis_title_font = {'size': 24}

app.css.append_css({
    'external_url': (
        'https://raw.githubusercontent.com/plotly/datasets/master/dash-css/stylesheet-oil-and-gas.css'
    )
})

@app.callback(
    Output('recommendation-table', 'data'),
    Input('otimizar-button', 'n_clicks'),
    State('weight-projects-input', 'value'),
    State('weight-hours-input', 'value'),
    State('weight-cost-input', 'value'),
    State('number-recommendations-input', 'value'),
    prevent_initial_call=True
)
def optimize_allocation(n_clicks, weight_projects, weight_hours, weight_cost, number_recommendations):
    global df_alocacoes

    allocation_df = df_alocacoes 
    df_recommendation = pd.DataFrame()
    nr_of = False
    df = gerar_visao_macro()

    if number_recommendations is None:
        number_recommendations = 1

    if n_clicks > 0:
        
        # Certifique-se de ajustar o código de otimização aqui
        for projeto in allocation_df['PROJETO_ID'].value_counts().index:
            print('\n *** ' + projeto + ' *** \n')
            squad = allocation_df[allocation_df['PROJETO_ID'] == projeto]

            df_opt = df.copy()
            df_opt_ori = df.copy()
            
            # Normaliza as colunas em df_opt
            max_hora_alocada = df_opt['col_hora_alocada'].max()
            max_custo_hora = df_opt['col_custo_hora'].max()
            max_number_proj = df_opt['col_number_proj'].max()

            df_opt['col_hora_alocada'] = df_opt['col_hora_alocada'] / max_hora_alocada
            df_opt['col_custo_hora'] = df_opt['col_custo_hora'] / max_custo_hora
            df_opt['col_number_proj'] = df_opt['col_number_proj'] / max_number_proj

            try:
                if weight_projects < 0:
                    weight_projects = 1

                if weight_hours < 0:
                    weight_hours = 1

                if weight_cost < 0:
                    weight_cost = 1
            except:
                weight_cost = 1
                weight_hours = 1
                weight_projects = 1

            # Defina os pesos para priorização
            weights = {
                "minimize_projects": weight_projects,
                "minimize_hours": weight_hours,
                "minimize_cost": weight_cost
            }
            
            for nr in range(0, number_recommendations):
                squad_allocator = SquadAllocatorLP(df_opt)
                squad_allocator.set_weights(weights)

                for index in squad.index:
                    collaborator = allocation_df.iloc[index, :]
                    squad_allocator.add_squad_requirement(
                        collaborator['CARGO'], collaborator['SETOR'], collaborator['CLASSE'],
                        collaborator['QUANTIDADE'], collaborator['HORAS'], collaborator['PROJETOS'],
                        collaborator['CUSTO']
                    )
                
                # Otimize a alocação
                try:
                    squad_allocator.optimize()
                    allocation_results = squad_allocator.get_allocation_results()

                    vet_collaborator = []

                    for collaborator, allocation_value in allocation_results:
                        vet_collaborator.append(collaborator)

                    print(vet_collaborator)
                    allocated_indices_LP = [df[df['col_nome'] == collaborator].index[0] for collaborator in vet_collaborator]

                    if not (nr_of):
                        df_recommendation = df_opt_ori[df_opt_ori['col_nome'].isin(vet_collaborator)]
                        df_recommendation['PROJETO_ID'] = [projeto] * len(df_recommendation)
                        df_recommendation['RECOMENDACAO_PRIORIDADE'] = ['ALLOCATION_' + str(nr + 1)] * len(df_recommendation)
                        df_opt = df_opt[~df_opt['col_nome'].isin(vet_collaborator)]
                        nr_of = True

                    else:
                        df_opt_aux = df_opt_ori[df_opt_ori['col_nome'].isin(vet_collaborator)]
                        df_opt_aux['PROJETO_ID'] = [projeto] * len(df_opt_aux)
                        df_opt_aux['RECOMENDACAO_PRIORIDADE'] = ['ALLOCATION_' + str(nr + 1)] * len(df_opt_aux)
                        df_recommendation = pd.concat([df_recommendation, df_opt_aux], axis=0, ignore_index=True)
                        df_opt = df_opt[~df_opt['col_nome'].isin(vet_collaborator)]
                except:
                    try:
                        squad_allocator = SquadAllocatorLP(df_opt)
                        squad_allocator.set_weights(weights)
                        for index in squad.index:
                            collaborator = allocation_df.iloc[index, :]
                            squad_allocator.add_squad_requirement(
                                collaborator['CARGO'], collaborator['SETOR'], collaborator['CLASSE'],
                                collaborator['QUANTIDADE'], 120, 40,300
                            )
                            try:
                                squad_allocator.optimize()
                                allocation_results = squad_allocator.get_allocation_results()

                                vet_collaborator = []

                                for collaborator, allocation_value in allocation_results:
                                    vet_collaborator.append(collaborator)

                                print(vet_collaborator)
                                allocated_indices_LP = [df[df['col_nome'] == collaborator].index[0] for collaborator in vet_collaborator]

                                if not (nr_of):
                                    df_recommendation = df_opt_ori[df_opt_ori['col_nome'].isin(vet_collaborator)]
                                    df_recommendation['PROJETO_ID'] = [projeto] * len(df_recommendation)
                                    df_recommendation['RECOMENDACAO_PRIORIDADE'] = ['ALLOCATION_' + str(nr + 1)] * len(df_recommendation)
                                    df_opt = df_opt[~df_opt['col_nome'].isin(vet_collaborator)]
                                    nr_of = True

                                else:
                                    df_opt_aux = df_opt_ori[df_opt_ori['col_nome'].isin(vet_collaborator)]
                                    df_opt_aux['PROJETO_ID'] = [projeto] * len(df_opt_aux)
                                    df_opt_aux['RECOMENDACAO_PRIORIDADE'] = ['ALLOCATION_' + str(nr + 1)] * len(df_opt_aux)
                                    df_recommendation = pd.concat([df_recommendation, df_opt_aux], axis=0, ignore_index=True)
                                    df_opt = df_opt[~df_opt['col_nome'].isin(vet_collaborator)]
                            except:
                                continue
                    except:
                        pass

        print(df_recommendation.head())
        return df_recommendation.to_dict('records')
        
@app.callback(
    [Output('otimizar-button', 'disabled')],
    Input('allocation-table', 'data'),
    prevent_initial_call=True
)
def enable_optimize_button(data):
    return [False] if data else [True]  # Habilita o botão se houver pelo menos uma linha na tabela

@app.callback(
    [Output('upload-data', 'children'),
     Output('csv-data-store', 'data'),
     Output('allocation-table', 'data', allow_duplicate=True)],  # Adicione uma saída para a tabela
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def update_uploaded_file(contents, filename):
    global df_alocacoes

    data = gerar_visao_macro()
    if contents is None:
        raise PreventUpdate

    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))

    # Verifica se as colunas são adequadas
    if set(df.columns) != {'PROJETO_ID', 'CARGO', 'SETOR', 'CLASSE', 'QUANTIDADE', 'HORAS', 'PROJETOS', 'CUSTO'}:
        return "O arquivo CSV não possui as colunas corretas.", csv_data.to_dict('records'), df_alocacoes.to_dict('records')

    analysis_result = df
    df_alocacoes = pd.concat([df_alocacoes, df], ignore_index=True)
    
    return "Arquivo CSV carregado com sucesso.", analysis_result.to_dict('records'), df_alocacoes.to_dict('records')
    
@app.callback(
    Output('allocation-table', 'data', allow_duplicate=True),
    Input('add-allocation-button', 'n_clicks'),
    State('cargo-dropdown', 'value'),
    State('setor-dropdown', 'value'),
    State('classe-dropdown', 'value'),
    State('horas-input', 'value'),
    State('projetos-input', 'value'),
    State('custo-input', 'value'),
    State('nome-projeto-input', 'value'),
    State('quantidade-col-input', 'value'),
    prevent_initial_call='initial_duplicate'
)
def adicionar_alocacao(n_clicks, cargo, setor, classe, horas, projetos, custo, nome_projeto, quantidade):
    if n_clicks is None:
        raise PreventUpdate  # Evita que a callback seja acionada antes do clique no botão

    if not cargo or not setor or not classe or horas is None or projetos is None or custo is None or not nome_projeto:
        # Verifica se algum campo não foi preenchido e retorna uma mensagem de erro
        return dash.no_update

    nova_alocacao = {
        'PROJETO_ID': [nome_projeto],
        'CARGO': [cargo],
        'SETOR': [setor],
        'CLASSE': [classe],
        'QUANTIDADE': [quantidade],
        'HORAS': [horas],
        'PROJETOS': [projetos],
        'CUSTO': [custo]
    }

    global df_alocacoes
    df_alocacoes = pd.concat([df_alocacoes, pd.DataFrame(nova_alocacao)], ignore_index=True)

    return df_alocacoes.to_dict('records')

@app.callback(
    Output('table2', 'data'),
    Output('table2', 'style_data_conditional'),
    Input('heatmap-column', 'value')
)
def update_heatmap(selected_column):
    data = gerar_visao_macro()
    data_styles = []

    max_value = data[selected_column].max()
    min_value = data[selected_column].min()

    for _, row in data.iterrows():
        cell_value = row[selected_column]
        color = 'rgb(255, 0, 0)'  # Red
        if max_value != min_value:
            color = f'rgb({int(255 * (cell_value - min_value) / (max_value - min_value))}, 0, {int(255 - 255 * (cell_value - min_value) / (max_value - min_value))})'

        data_styles.append({
            'if': {'filter_query': f'{{{selected_column}}} eq {cell_value}'},
            'backgroundColor': color,
            'color': 'white',
            'textAlign': 'center',
            'font-family': 'Verdana'
        })

    return data.to_dict('records'), data_styles

if __name__ == '__main__':
    app.run_server(debug=False, port=8090)