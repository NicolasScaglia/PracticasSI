import json
from queue import PriorityQueue
import datetime
from geopy import distance
from timeit import default_timer as timer
from abc import ABC, abstractmethod
import random


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
        self.numero_estaciones = self.data['number_stations']
        self.candidatos = self.data['candidates']
        self.calcular_acciones()
        self.calcular_estados()

    def set_estado_final(self, estado):
        self.estado_final = estado
    def set_estado_inicial(self, estado):
        self.estado_inicial = estado
    
    # Diccionario de acciones para calcular las conexiones entre intersecciones
    def calcular_acciones(self):
        self.acciones = {}
        self.velocaidad_media = 0
        self.velocidad_maxima = 0
        cuenta = 0
        self.data['segments'].sort(key = lambda a : a['destination'])
        for element in self.data['segments']:
            if element['origin'] not in self.acciones:
                self.acciones[element['origin']] = []
            self.acciones[element['origin']].append(Accion(element['origin'], element['destination'], element['distance'], element['speed']))
        self.velocaidad_media /= cuenta
        
    # Diccionario de estados, id del estado, estado en el otro lado
    def calcular_estados(self):
        self.estados = {}
        for element in self.data['intersections']:
            self.estados[element['identifier']] = Estado(element['identifier'], element['longitude'], element['latitude'])
    
class Heuristica():
    def __init__(self, valor):
        self.heuristica = valor
    
    def funcion_heuristica(self, posicionActual, posicionFinal):
        return distance.distance(posicionActual, posicionFinal).m / toMetersPerSecond(self.heuristica)

class Busqueda(ABC):

    generados = 0
    expandidos = 0
    explorados = 0
    coste = 0
    
    def __init__(self, problema, frontera):
        self.problema = problema
        self.frontera = frontera

    def start(self):
        start = timer() 
        self.solucion = self.algoritmo()
        if self.solucion is not None:
            self.coste = self.solucion.coste
        end = timer()
        self.tiempoEjecucion = end - start
        self.problema.calcular_acciones()
        
    def algoritmo(self):
        self.cerrados = set()
        nodoInicial = Nodo(self.problema.inicial, None, None)
        self.insertar(nodoInicial)
        while(True):
            if self.es_vacia():
                print("[INFO] No se ha encontrado solución\n")
                return self.nodoActual
            self.nodoActual = self.sacar_siguiente()
            if self.es_final():
                self.explorados += 1
                return self.nodoActual
            self.explorados += 1
            if self.nodoActual.estado not in self.cerrados:
                self.cerrados.add(self.nodoActual.estado)
                self.abrir_nodo()

    @abstractmethod
    def insertar(self, nodo):
        pass
    
    def es_vacia(self):
        return not self.frontera
    
    @abstractmethod
    def sacar_siguiente(self):
        pass    

    def es_final(self):
        NotImplemented

    def abrir_nodo(self):
        self.expandidos += 1
        if self.nodoActual.estado.identificador in self.problema.acciones:
            acciones = self.problema.acciones[self.nodoActual.estado.identificador]
        else:
            return
        for element in acciones:
            accion = element
            nodoFrontera = Nodo(self.problema.estados[accion.destino], self.nodoActual, accion)
            self.insertar(nodoFrontera)
            self.generados += 1


def evaluacion(solucion, problema):
    sumPop = 0
    min = -112
    for element in problema.candidatos:
        for i in range(0, len(solucion) - 1):
            if solucion == 1:
                problema.set_estado_inicial(element[0])
                problema.set_estado_final(problema.candidatos[i][0])
                estrella = AE(problema, Heuristica())
                estrella.start()
                if estrella.solucion.coste * element[1] < min or min < 0:
                    min = estrella.solucion.coste * element[1]
        sumPop += element[1]
    return (1/sumPop) * min

            
class Individuo():

    # Cadena genética representa la solución del individuo.
    # Tamaño representa el tamaño de la cadena genética.
    # Todo individuo tiene un valor de fitness, o lo que es lo mismo
    # un valor de aptitud.
    def __init__(self, cadena_genetica=None, tamano=1, seleccionados=1):
        if cadena_genetica is None:
            # Si no se pasa una cadena genética en concreto, usamos el resto de parámetros
            # siempre y cuando sean válidos para generar una.
            if tamano < 1 or seleccionados < 1:
                return
            self.seleccionados = seleccionados
            self.tamano = tamano
            # Inicializamos la cadena genética sin ninguna selección.
            self.cadena_genetica = [0] * tamano
            # La función generar hace una selección aleatoria de @seleccionados elementos.
            self.generar()
        else:
            # Si pasan una cadena genética, obtenemos los parámetros de ésta.
            self.cadena_genetica = cadena_genetica
            self.tamano = len(self.cadena_genetica)
            self.seleccionados = self.cadena_genetica.count(1)

        self.fitness = 0

    def evaluar(self, problema):
        # Evaluamos al individuo usando la función de evaluación
        self.fitness = evaluacion(self.cadena_genetica, problema)

    def cruzar(self, otro, probabilidad=1.0):
        pass

    def mutar(self, probabilidad=1.0):
        pass
    
    def generar(self):
        # Mientras que no haya el número de 1s (seleccionados) igual a
        # el número de seleccionados que necesitamos, continuamos.
        while self.cadena_genetica.count(1) != self.seleccionados:
            pos = random.randint(0, len(self.cadena_genetica) - 1)
            if self.cadena_genetica[pos] != 1:
                self.cadena_genetica[pos] = 1

class AlgoritmoAleatorio():


    # Se debe pasar el problema en concreto y el tamaño de la población
    # al algoritmo.
    def __init__(self, problema, tamano_poblacion = 100):
        self.problema = problema
        self.tamano_poblacion = tamano_poblacion

        # Utilizamos una caché para que si ya tenemos un resultado, no volver
        # a realizar una evaluación innecesaria. Key = toString(cadena_genética),
        # Value = fitness 
        self.cache = {}
    
    def algoritmo(self):

        # Inicializamos el mejor individuo a nulo.
        mejor_individuo = None

        # Hacemos un bucle que dure el tamaño de la población.
        for i in range(self.tamano_poblacion):

            # Generamos el individuo en el momento en vez de guardarlo en un array, así
            # ahorramos memoria.
            temp = Individuo(tamano=len(self.problema.candidatos), seleccionados=self.problema.num_estaciones)

            # Variable fitness temporal.
            fitness = 0

            # Acceso a la caché (simplifica la lectura del código).
            acceso = self.cache[temp.cadena_genetica.__str__()]

            # Si existe valor en caché, usamos ese y no evaluamos de nuevo.
            if acceso != None:
                fitness = acceso
            else:
                # Si no, fitness será el valor de la evaluación y la guardamos en caché.
                fitness = temp.evaluar(self.problema)
                self.cache[temp.cadena_genetica.__str__()] = fitness

            # Actualizamos el mejor valor.
            if mejor_individuo.fitness < fitness or mejor_individuo is None:
                mejor_individuo = temp
            
            # Devolvemos el mejor individuo.
        return mejor_individuo




class AE(Busqueda):

    def __init__(self, problema, heuristica):
        frontera = PriorityQueue()
        super().__init__(problema, frontera)
        self.heuristica = heuristica

    def insertar(self, nodo):
        self.frontera.put(())

    def sacar_siguiente(self):
        return self.frontera.get()[1]

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
    prob = Problema("examples_with_solutions/problems/huge/calle_agustina_aroca_albacete_5000_0.json")
    heur = Heuristica(prob.velocidad_maxima)
    print("A*: ")
    aestrella = AE(prob, heur)
    aestrella.start()

if __name__ == "__main__":
    main()

