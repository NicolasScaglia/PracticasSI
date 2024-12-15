import json
from queue import PriorityQueue
import random
from geopy import distance
from abc import ABC, abstractmethod
from math import sqrt


def load_data(fileName):
    if not fileName.endswith(".json"):
        print("El archivo no es válido.")
        return
    with open(fileName, 'r') as file:
        data = json.load(file)
    return data

class Estado:

    def __init__(self, id, long, lat):
        self.identificador = id
        self.longitud = long
        self.latitud = lat

class Accion:

    def __init__(self, orig, dest, dist, vel):
        self.origen = orig
        self.destino = dest
        self.coste = dist / toMetersPerSecond(vel)
    
    def __lt__(self, otro):
        return self.destino < otro.destino

class Nodo:

    def __init__(self, est, pad, acc):
        self.estado = est
        self.padre = pad
        self.accion = acc
        if self.padre is not None and self.accion is not None:
            self.profundidad = self.padre.profundidad + 1
            self.coste = self.padre.coste + self.accion.coste
        else:
            self.profundidad = 0
            self.coste = 0

    def __lt__(self, otro):
        return self.estado.identificador < otro.estado.identificador

class Problema:

    def __init__(self, problemName):
        self.problemName = problemName
        self.data = load_data(self.problemName)
        if not self.data:
            print("[ERROR] No se ha encontrado la información del problema.")
            return
        # Encontramos el estado final y el estado inicial en el diccionario de estados
        self.calcular_acciones()
        self.calcular_estados()
        self.candidatos = self.data['candidates']
        self.numero_estaciones = self.data['number_stations']
    
    # Diccionario de acciones para calcular las conexiones entre intersecciones
    def calcular_acciones(self):
        self.acciones = {}
        self.velocidad_maxima = 0
        for element in self.data['segments']:
            if element['origin'] not in self.acciones:
                self.acciones[element['origin']] = []
            self.acciones[element['origin']].append(Accion(element['origin'], element['destination'], element['distance'], element['speed']))
            if element['speed'] > self.velocidad_maxima:
                self.velocidad_maxima = element['speed']


    # Diccionario de estados, id del estado, estado en el otro lado
    def calcular_estados(self):
        self.estados = {}
        for element in self.data['intersections']:
            self.estados[element['identifier']] = Estado(element['identifier'], element['longitude'], element['latitude'])
    
class Heuristica():
    def __init__(self, valor):
        self.heuristica = valor
    
    def funcion_heuristica(self, latitudFinal, latitudInicial, longitudFinal, longitudInicial):
        return sqrt((abs(latitudFinal - latitudInicial)**2 + abs(longitudFinal - longitudInicial)**2)) / toMetersPerSecond(self.heuristica)

class Busqueda(ABC):

    
    def __init__(self, problema, frontera):
        self.problema = problema
        self.frontera = frontera

    def start(self):
        self.solucion = self.algoritmo()
        
    def algoritmo(self):
        self.cerrados = set()
        nodoInicial = Nodo(self.problema.estado_inicial, None, None)
        self.insertar(nodoInicial)
        while(True):
            if self.es_vacia():
                return 3600*5
            self.nodoActual = self.sacar_siguiente()
            if self.es_final():
                return self.nodoActual.coste
            if self.nodoActual.estado not in self.cerrados:
                self.cerrados.add(self.nodoActual.estado)
                self.abrir_nodo()

    @abstractmethod
    def insertar(self, nodo):
        pass
    
    def es_vacia(self):
        return self.frontera.empty()
    
    @abstractmethod
    def sacar_siguiente(self):
        pass    

    def es_final(self):
        return self.nodoActual.estado == self.problema.estado_final

    def abrir_nodo(self):
        if self.nodoActual.estado.identificador in self.problema.acciones:
            acciones = self.problema.acciones[self.nodoActual.estado.identificador]
        else:
            return
        for element in acciones:
            accion = element
            nodoFrontera = Nodo(self.problema.estados[accion.destino], self.nodoActual, accion)
            self.insertar(nodoFrontera)

class AE(Busqueda):

    def __init__(self, problema, heuristica):
        frontera = PriorityQueue()
        super().__init__(problema, frontera)
        self.heuristica = heuristica

    def insertar(self, nodo):
        prioridad = self.heuristica.funcion_heuristica(self.problema.estado_final.latitud, nodo.estado.latitud, self.problema.estado_final.longitud, nodo.estado.longitud) + nodo.coste
        self.frontera.put((prioridad, nodo))

    def sacar_siguiente(self):
        return self.frontera.get()[1]


class Individuo():

    cache = {}
    hits = 0
    misses = 0

    def __init__(self, seleccionados=None, candidatos=[], tamano=0):
        if seleccionados is None:
            self.seleccionados = tuple()
            self.generar(candidatos, tamano)
        else:
            self.seleccionados = tuple(seleccionados)
        self.candidatos = candidatos
        self.tamano = tamano

    def evaluar(self, problema):
        sumPop = 0
        aux = 0
        estrella = AE(problema, Heuristica(problema.velocidad_maxima))

        for candidato in problema.candidatos:
            minimum = 3600*5
            for solucion in self.seleccionados:
                tupla = (candidato[0], solucion)
                if tupla in Individuo.cache:
                    val = Individuo.cache[tupla]
                    Individuo.hits += 1
                else:
                    estrella.problema.estado_inicial = problema.estados[candidato[0]]
                    estrella.problema.estado_final = problema.estados[solucion]
                    estrella.start()
                    val = estrella.solucion
                    Individuo.cache[tupla] = val
                    Individuo.misses += 1
                minimum = min(val, minimum)
            sumPop += candidato[1]
            aux += candidato[1]*minimum
        self.fitness = (1/sumPop) * aux

    def cruzar(self, otro, probabilidad=1.0):

        if random.random() < probabilidad:
            corte = random.randint(1, len(self.seleccionados) - 1)
            piscina_genetica = self.seleccionados + otro.seleccionados
            hijo1 = list(self.seleccionados[corte:] + otro.seleccionados[:corte])
            hijo2 = list(otro.seleccionados[corte:] + self.seleccionados[:corte])
            if len(hijo1) < len(self.seleccionados):
                faltantes = len(self.seleccionados) - len(hijo1)
                hijo1.append(x for x in random.sample(piscina_genetica - hijo1, faltantes))
            if len(hijo2) < len(self.seleccionados):
                faltantes = len(self.seleccionados) - len(hijo2)
                hijo1.append(x for x in random.sample(piscina_genetica - hijo2, faltantes))
        else:
            hijo1 = self.seleccionados
            hijo2 = otro.seleccionados

        return (Individuo(hijo1, candidatos=self.candidatos), Individuo(hijo2, candidatos=self.candidatos))
                    
    def mutar(self, probabilidad=1.0):
        # Aplica una mutación a partir de una probabildad dada.
        aux = list(self.seleccionados)
        for _ in range(len(self.seleccionados)):
            if random.random() < probabilidad:
                nuevo = random.choice(self.candidatos)[0]
                while nuevo in aux:
                    nuevo = random.choice(self.candidatos)[0]
                aux.remove(random.choice(aux))
                aux.append(nuevo)
        self.seleccionados = tuple(aux)
    
    def generar(self, candidatos, tamano):
        list = random.sample(candidatos, tamano)
        self.seleccionados = tuple(x[0] for x in list)


class AlgoritmoAleatorio():

    cache = {}

    def __init__(self, problema, tamano_poblacion=100):
        self.problema = problema
        self.tamano_poblacion = tamano_poblacion

    def algoritmo(self):
        mejor_individuo = None

        for i in range(self.tamano_poblacion):
            temp = Individuo(candidatos=self.problema.candidatos, tamano=self.problema.numero_estaciones)

            acceso = temp.seleccionados

            if acceso in AlgoritmoAleatorio.cache:
                fitness = AlgoritmoAleatorio.cache[acceso]
            else:
                temp.evaluar(self.problema)
                fitness = temp.fitness
                AlgoritmoAleatorio.cache[acceso] = fitness
            
            if mejor_individuo is None:
                mejor_individuo = temp
            
            if mejor_individuo.fitness > fitness:
                mejor_individuo = temp

        return mejor_individuo


class AlgoritmoGenetico:

    cache = {}

    def __init__(self, problema, tamano_poblacion=100, generaciones=50, probabilidad_cruce=0.777, probabilidad_mutacion=0.777):
        self.problema = problema
        self.tamano_poblacion = tamano_poblacion
        self.generaciones = generaciones
        self.probabilidad_cruce = probabilidad_cruce
        self.probabilidad_mutacion = probabilidad_mutacion

    def seleccionar_rango(self, poblacion):

        N = len(poblacion)
        seleccionados = []

        prob = [2 * (N - i + 1) / (N**2 + N) for i in range(0, N)]

        seleccionados = random.choices(population=poblacion, weights=prob, k=random.randint(5, N))

        return seleccionados

    def seleccionar_torneo(self, poblacion, k=2):
        seleccionados = []
        for _ in range(len(poblacion)):
            torneo = random.sample(poblacion, k)
            ganador = max(torneo, key=lambda i : i.fitness)
            seleccionados.append(ganador)
        return seleccionados



    def algoritmo(self):


        condicion_de_parada = False

        convergencia = float('inf')

        anterior = None
        
        #t = 0
        numero_de_generaciones = 0


        mejor_individuo = None


        # inicializar P(t)
        poblacion = [Individuo(candidatos=self.problema.candidatos, tamano=self.problema.numero_estaciones) for _ in range(self.tamano_poblacion) ]

        # evaluar P(t)
        for element in poblacion:
            acceso = element.seleccionados
            if acceso in AlgoritmoGenetico.cache:
                element.fitness = AlgoritmoGenetico.cache[acceso]
            else:
                element.evaluar(self.problema)
                AlgoritmoGenetico.cache[acceso] = element.fitness
        
        poblacion.sort(key=lambda i : i.fitness, reverse=True)

        while not condicion_de_parada:
            numero_de_generaciones += 1
            # poblacion_auxiliar = self.seleccionar_torneo(poblacion, random.randint(1, self.tamano_poblacion))
            poblacion_auxiliar = self.seleccionar_torneo(poblacion, random.randint(2, len(poblacion)))

            nueva_poblacion = []

            N = self.tamano_poblacion
            for i in range(0, len(poblacion_auxiliar), 2):
                if i + 1 < len(poblacion_auxiliar):
                    
                    hijos = poblacion_auxiliar[i].cruzar(poblacion_auxiliar[i+1], probabilidad=self.probabilidad_cruce)
                    hijo1 = hijos[0]
                    hijo2 = hijos[1]

                    hijo1.mutar(self.probabilidad_mutacion)
                    hijo2.mutar(self.probabilidad_mutacion)

                    acceso1 = hijo1.seleccionados
                    if acceso1 in AlgoritmoGenetico.cache:
                        hijo1.fitness = AlgoritmoGenetico.cache[acceso1]
                    else:
                        hijo1.evaluar(self.problema)
                        AlgoritmoGenetico.cache[acceso1] = hijo1.fitness

                    acceso2 = hijo2.seleccionados
                    if acceso2 in AlgoritmoGenetico.cache:
                        hijo2.fitness = AlgoritmoGenetico.cache[acceso2]
                    else:
                        hijo2.evaluar(self.problema)
                        AlgoritmoGenetico.cache[acceso2] = hijo2.fitness

                    nueva_poblacion.extend([hijo1, hijo2])

                else:
                    nueva_poblacion.append(poblacion_auxiliar[i])

            combinada = poblacion + nueva_poblacion


            poblacion = sorted(combinada, key= lambda i : i.fitness, reverse=True)[:self.tamano_poblacion]

            if mejor_individuo is None:
                mejor_individuo = poblacion[0]
            elif mejor_individuo.fitness < poblacion[0].fitness:
                mejor_individuo = poblacion[0]

            if anterior is not None:
                dif = list(set(poblacion) - anterior)
                convergencia = len(dif)
            
            anterior = set(poblacion)

            print(f"Generación: {numero_de_generaciones}")
            print(f"Mejor Individuo: {mejor_individuo.seleccionados}")
            print(f"Convergencia: {convergencia}")
            print(f"Hits en caché Individuo: {Individuo.hits}")
            print(f"Fallos en caché Individuo: {Individuo.misses}")

            condicion_de_parada = self.tamano_poblacion - convergencia >= 0.1*self.tamano_poblacion


        return mejor_individuo
                
            




# def imprimirResultado(busqueda):
#     print(f"Nodos generados: {busqueda.generados}")
#     print(f"Nodos expandidos: {busqueda.expandidos}")
#     print(f"Nodos explorados: {busqueda.explorados}")
#     tiempo = datetime.timedelta(seconds=busqueda.tiempoEjecucion)
#     print(f"Duración de la ejecución: {tiempo}")
#     coste = datetime.timedelta(seconds=busqueda.coste)
#     print(f"Coste final: {coste}")
#     reconstruirCamino(busqueda.solucion)

# def reconstruirCamino(nodo):
#     if nodo is None:
#         return
#     ids = [nodo.estado.identificador]
#     while nodo.padre is not None:
#         nodo = nodo.padre
#         ids.append(nodo.estado.identificador)
#     ids.reverse()
#     print(f"Longitud de la solucion: {len(ids)}")
#     print(f"Camino recorrido: {ids}")




def toMetersPerSecond(kilometersPerHour):
    return (kilometersPerHour * 1000) / 3600

def main():
    prob = Problema("P2_SI/sample-problems-lab2/medium/calle_iÌnsula_barataria_albacete_500_0_candidates_140_ns_34.json")
    # AA = AlgoritmoAleatorio(prob)
    # print(AA.algoritmo().seleccionados)
    # print("-------------------------------------------------------------------")
    AG = AlgoritmoGenetico(prob, 100)
    print(f"Solución: {AG.algoritmo().seleccionados}")

if __name__ == "__main__":
    main()

