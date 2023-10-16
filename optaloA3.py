import numpy as np
import pandas as pd

from scipy.optimize import linprog

import random
from deap import base, creator, tools, algorithms

import numpy as np
from scipy.optimize import linprog

class SquadAllocatorLP:
    def __init__(self, df, method='highs'):
        self.df = df
        self.squad_requirements = []
        self.allocation = []
        self.weights = {"minimize_projects": 1.0, "minimize_hours": 1.0, "minimize_cost": 1.0}
        self.hire_required = {}  # Dicionário para indicar se a contratação é necessária para cada cargo
        self.method = method

    def add_squad_requirement(self, cargo, setor, classe, quantidade, horas_maximas, projetos_maximos, custo_maximo):
        self.squad_requirements.append({"cargo": cargo, "setor": setor, "classe": classe, "quantidade": quantidade, "horas_maximas": horas_maximas, "projetos_maximos": projetos_maximos, "custo_maximo": custo_maximo})

    def set_weights(self, weights):
        self.weights = weights

    def optimize(self):
        # Converter os dados do DataFrame em matrizes
        projetos = self.df["col_number_proj"].values
        horas_disponiveis = self.df["col_hora_alocada"].values
        custo_hora = self.df["col_custo_hora"].values

        # Inicializar A_eq como uma matriz vazia
        A_eq = np.empty((0, len(self.df)))

        # Vetor b_eq
        b_eq = []

        # Inicializar A_ub como uma matriz vazia
        A_ub = np.empty((0, len(self.df)))

        # Vetor b_ub
        b_ub = []

        for req in self.squad_requirements:
            indices = [
                j
                for j, row in enumerate(self.df["col_cargo"])
                if row == req['cargo'] and
                   self.df["col_setor"].values[j] == req['setor'] and
                   self.df["col_classe"].values[j] == req['classe']
            ]
            # Adicione uma nova linha de restrição
            A_new = np.zeros((1, len(self.df)))
            A_new[0, indices] = 1
            A_eq = np.vstack((A_eq, A_new))
            b_eq.append(req['quantidade'])

            hire_required = False  # Variável para indicar se contratação é necessária para este cargo

            for i in indices:
                # Adicionar restrição de número máximo de projetos individual
                A_projeto_max_individual = np.zeros((1, len(self.df)))
                A_projeto_max_individual[0, i] = 1
                A_ub = np.vstack((A_ub, A_projeto_max_individual))
                b_ub.append(req['projetos_maximos'])

                # Adicionar restrição de custo máximo individual
                A_custo_max_individual = np.zeros((1, len(self.df)))
                A_custo_max_individual[0, i] = req['custo_maximo']
                A_ub = np.vstack((A_ub, A_custo_max_individual))
                b_ub.append(req['custo_maximo'])

                # Adicionar restrição de horas máximas individual
                A_horas_max_individual = np.zeros((1, len(self.df)))
                A_horas_max_individual[0, i] = req['horas_maximas']
                A_ub = np.vstack((A_ub, A_horas_max_individual))
                b_ub.append(req['horas_maximas'])

                # Verificar se a contratação é necessária para este cargo
                if i not in self.allocation:
                    hire_required = True

            self.hire_required[req['cargo']] = hire_required

        # Converter b_eq para um array NumPy
        b_eq = np.array(b_eq)
        b_ub = np.array(b_ub)

        # Definir os limites das variáveis
        bounds = [(0, 1)] * len(self.df)

        # Multiplicar os pesos pelas variáveis
        c = (
            self.weights["minimize_projects"] * projetos +
            self.weights["minimize_hours"] * horas_disponiveis +
            self.weights["minimize_cost"] * custo_hora
        )

        # Resolver o problema de otimização
        result = linprog(c, A_eq=A_eq, b_eq=b_eq, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method=self.method)

        # Obter o resultado da alocação
        self.allocation = [(self.df["col_nome"].values[i], result.x[i]) for i in range(len(result.x)) if result.x[i] > 0]

    def get_allocation_results(self):
        return self.allocation

    def is_hire_required(self, cargo):
        return self.hire_required.get(cargo, False)

class SquadAllocatorGA:
    def __init__(self, df):
        self.df = df
        self.weights = {
            "minimize_projects": 1.0,
            "minimize_hours": 1.0,
            "minimize_cost": 1.0,
            "maximize_hours_sold": 1.0
        }
        self.squad_requirements = []

    def set_weights(self, weights):
        self.weights = weights

    def fitness(self, individual):
        allocation = np.array(individual)
        horas_disponiveis = self.df["col_hora_alocada"].values
        projetos = self.df["col_number_proj"].values
        custo_hora = self.df["col_custo_hora"].values

        score = (
            self.weights["minimize_projects"] * np.sum(projetos * allocation) +
            self.weights["minimize_hours"] * np.sum(horas_disponiveis * allocation) +
            self.weights["minimize_cost"] * np.sum(custo_hora * allocation)
        )

        return (score,)

    def add_squad_requirement(self, cargo, setor, classe, quantidade, horas_vendidas):
        self.squad_requirements.append((cargo, setor, classe, quantidade, horas_vendidas))

    def evaluate(self, individual):
        allocation = np.array(individual)
        horas_disponiveis = self.df["col_hora_alocada"].values
        projetos = self.df["col_number_proj"].values
        custo_hora = self.df["col_custo_hora"].values

        score = (
            self.weights["minimize_projects"] * np.sum(projetos * allocation) +
            self.weights["minimize_hours"] * np.sum(horas_disponiveis * allocation) +
            self.weights["minimize_cost"] * np.sum(custo_hora * allocation)
        )

        return (score,)

    def optimize(self, population_size=50, generations=50, crossover_prob=0.7, mutation_prob=0.2):
        random.seed(42)

        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)

        toolbox = base.Toolbox()
        toolbox.register("attr_bool", random.randint, 0, 1)
        toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_bool, n=len(self.df))
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        toolbox.register("mate", tools.cxTwoPoint)
        toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)
        toolbox.register("select", tools.selTournament, tournsize=3)
        toolbox.register("evaluate", self.evaluate)

        population = toolbox.population(n=population_size)

        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", np.mean)
        stats.register("min", np.min)

        algorithms.eaMuPlusLambda(
            population, toolbox, mu=population_size//2, lambda_=population_size//2, cxpb=crossover_prob, mutpb=mutation_prob, ngen=generations, stats=stats, halloffame=None
        )

        best_individual = tools.selBest(population, 1)[0]

        allocation_results = self.allocate_collaborators(best_individual)

        return allocation_results

    def allocate_collaborators(self, individual):
        allocation_results = []
        squad_counts = {req[0]: req[3] for req in self.squad_requirements}

        for i, collaborator in enumerate(self.df["col_nome"].values):
            if individual[i]:
                cargo_colaborador = self.df["col_cargo"].values[i]

                if cargo_colaborador in squad_counts and squad_counts[cargo_colaborador] > 0:
                    allocation_results.append(f"{collaborator}")
                    squad_counts[cargo_colaborador] -= 1

                if not any(squad_counts.values()):  # Todas as posições do squad foram preenchidas
                    break

        return allocation_results