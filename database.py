import random
import csv
import pandas as pd

def gerar_visao_macro(filename="data_input/alocamento_colaboradores_projetos.csv"):
    # Carregue o arquivo alocamento_colaboradores_projetos.csv
    alocamentos = pd.read_csv(filename)

    # Agregue as informações com base na coluna "col_matricula"
    visao_macro = alocamentos.groupby('col_matricula').agg({
        'col_custo': 'first',  # Assume que o custo é o mesmo para todas as alocações do mesmo colaborador
        'col_cargo': 'first',  # Assume que o cargo é o mesmo para todas as alocações do mesmo colaborador
        'col_setor': 'first',  # Assume que o setor é o mesmo para todas as alocações do mesmo colaborador
        'col_classe': 'first',  # Assume que a classe é a mesma para todas as alocações do mesmo colaborador
        'pro_number': 'nunique',  # Conta o número de projetos únicos alocados
        'horas_aolocadas': 'sum'  # Soma o total de horas alocadas
    }).reset_index()

    # Renomeie as colunas conforme especificado
    visao_macro.rename(columns={
        'col_matricula': 'col_nome',
        'horas_aolocadas': 'col_hora_alocada',
        'col_custo': 'col_custo_hora',
        'pro_number': 'col_number_proj'
    }, inplace=True)

    # Reordene as colunas
    visao_macro = visao_macro[['col_nome', 'col_hora_alocada', 'col_custo_hora', 'col_number_proj', 'col_cargo', 'col_setor', 'col_classe']]

    return visao_macro

# Função para alocar colaboradores em projetos
def alocar_colaboradores(colaboradores, projetos):
    alocamentos = []
    
    for colaborador in colaboradores:
        num_projetos_aalocar = random.randint(1, 4)  # Aloque entre 1 e 4 projetos
        projetos_disponiveis = list(projetos)  # Crie uma cópia da lista de projetos disponíveis

        for _ in range(num_projetos_aalocar):
            if projetos_disponiveis:
                projeto = random.choice(projetos_disponiveis)
                pro_number = projeto[0]
                horas_disponiveis = projeto[1]
                horas_aolocadas = random.randint(10, min(horas_disponiveis, 40))
                
                # Obtenha informações do colaborador
                col_matricula, col_cargo, col_setor, col_classe, col_custo = colaborador

                # Registre o alocamento do colaborador no projeto com todas as informações
                alocamentos.append([col_matricula, col_cargo, col_setor, col_classe, pro_number, horas_aolocadas, col_custo])

                # Remova o projeto alocado da lista de projetos disponíveis
                projetos_disponiveis.remove(projeto)

    return alocamentos

# Função para gerar uma matrícula única
def gerar_matricula_unica():
    matricula = "MA" + str(random.randint(1000, 9999))
    while matricula in matriculas_usadas:
        matricula = "MA" + str(random.randint(1000, 9999))
    matriculas_usadas.add(matricula)
    return matricula


# Gere colaboradores aleatórios com pro_number e horas_alocadas
projetos = []

# Número total de pro_numbers
total_pro_numbers = 40

# Define os pro_numbers e gera as horas alocadas
pro_numbers = ["PR" + str(i) for i in range(1, total_pro_numbers + 1)]
for pro_number in pro_numbers:
    # Gere aleatoriamente quantas linhas para este pro_number (entre 2 e 8)
    num_linhas = random.randint(2, 8)
    # Gere aleatoriamente as horas alocadas para cada linha (não excedendo 80 horas)
    horas_restantes = 80
    for _ in range(num_linhas):
        horas = random.randint(15,40)
        projetos.append([pro_number, horas])
        horas_restantes -= horas

# Embaralhe a lista de colaboradores para torná-la aleatória
random.shuffle(projetos)

print("Base de dados de pro_numbers e horas_alocadas gerada com sucesso e salva como base_de_dados_pro_numbers_horas.csv.")

# Define os grupos
grupos = {
    "Grupo 1": {"Cargo": "Cientista de Dados", "Setor": "Cientista", "Classes": {"Junior": 16, "Pleno": 30, "Senior": 8, "Especialista": 4, "Tech Lead": 2}},
    "Grupo 2": {"Cargo": "Engenheiro de Dados", "Setor": "Engenheiro", "Classes": {"Junior": 25, "Pleno": 35, "Senior": 13, "Especialista": 5, "Tech Lead": 4}},
    "Grupo 3": {"Cargo": "Engenheiro de Machine Learning", "Setor": "EML", "Classes": {"Junior": 9, "Pleno": 12, "Senior": 3, "Especialista": 2, "Tech Lead": 1}},
    "Grupo 4": {"Cargo": "Analista de Dados", "Setor": "Analista", "Classes": {"Junior": 8, "Pleno": 15, "Senior": 8, "Especialista": 2, "Tech Lead": 2}}
}

# Gere colaboradores aleatórios com base nas distribuições e bônus de custo
colaboradores = []
matriculas_usadas = set()

# Bônus de custo para cada classe
bonus_custo = {
    "Junior": 10,
    "Pleno": 20,
    "Senior": 30,
    "Especialista": 40,
    "Tech Lead": 50
}

# Gere as matrículas aleatoriamente para cada classe em cada grupo
for grupo, detalhes_grupo in grupos.items():
    cargo = detalhes_grupo["Cargo"]
    setor = detalhes_grupo["Setor"]
    classes = detalhes_grupo["Classes"]
    for classe, quantidade in classes.items():
        for _ in range(quantidade):
            matricula = gerar_matricula_unica()
            col_custo = random.randint(20, 110) + bonus_custo[classe]  # Adicione o bônus ao custo
            colaboradores.append([matricula, cargo, setor, classe, col_custo])

# Embaralhe a lista de colaboradores para torná-la aleatória
random.shuffle(colaboradores)

# Realize a alocação de colaboradores em projetos
alocamentos = alocar_colaboradores(colaboradores, projetos)

# Salve os alocamentos em um arquivo CSV
with open("data_input/alocamento_colaboradores_projetos.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["col_matricula", "col_cargo", "col_setor", "col_classe", "pro_number", "horas_aolocadas", "col_custo"])
    writer.writerows(alocamentos)

ma = gerar_visao_macro()
print("Alocamento de colaboradores em projetos concluído e os dados salvos em alocamento_colaboradores_projetos.csv.")