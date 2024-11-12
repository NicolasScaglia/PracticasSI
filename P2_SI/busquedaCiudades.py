import json
from queue import PriorityQueue
import datetime
from geopy import distance
from timeit import default_timer as timer
from abc import ABC, abstractmethod


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
        self.estadoFinal = self.estados[self.data['final']]
        self.estadoInicial = self.estados[self.data['initial']]
        self.posicionFinal = (self.estadoFinal.latitud, self.estadoFinal.longitud)
    
    # Diccionario de acciones para calcular las conexiones entre intersecciones
    def calcular_acciones(self):
        acciones = {}
        self.acciones = {}
        self.velocaidad_media = 0
        self.velocidad_maxima = 0
        cuenta = 0
        for element in self.data['segments']:
            if element['origin'] not in acciones:
                acciones[element['origin']] = PriorityQueue()
                self.acciones[element['origin']] = []
            acciones[element['origin']].put((element['destination'],Accion(element['origin'], element['destination'], element['distance'], element['speed'])))
            if element['speed'] > self.velocidad_maxima:
                self.velocidad_maxima = element['speed']
            self.velocaidad_media += element['speed']
            cuenta += 1
        self.velocaidad_media /= cuenta

        for element in self.data['segments']:
            if element['origin'] in acciones:
                while not acciones[element['origin']].empty():
                    self.acciones[element['origin']].append(acciones[element['origin']].get()[1])
        
                    

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
        #self.problema.calcular_acciones()
        
    def algoritmo(self):
        self.cerrados = set()
        nodoInicial = Nodo(self.problema.estadoInicial, None, None)
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
        return self.nodoActual.estado == self.problema.estadoFinal

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

    
class BFS(Busqueda):

    def __init__(self, problema):
        frontera = []
        super().__init__(problema, frontera)

    def insertar(self, nodo):
        self.frontera.append(nodo)

    def sacar_siguiente(self):
        return self.frontera.pop(0)
    
class DFS(Busqueda):

    def __init__(self, problema):
        frontera = []
        super().__init__(problema, frontera)

    def insertar(self, nodo):
        self.frontera.append(nodo)

    def sacar_siguiente(self):
        return self.frontera.pop(len(self.frontera) - 1)

class PM(Busqueda):

    def __init__(self, problema, heuristica):
        frontera = PriorityQueue()
        super().__init__(problema, frontera)
        self.heuristica = heuristica

    def sacar_siguiente(self):
        return self.frontera.get()[1]
    
class AE(Busqueda):

    def __init__(self, problema, heuristica):
        frontera = PriorityQueue()
        super().__init__(problema, frontera)
        self.heuristica = heuristica

    def sacar_siguiente(self):
        return self.frontera.get()[1]

def imprimirResultado(busqueda):
    print(f"Nodos generados: {busqueda.generados}")
    print(f"Nodos expandidos: {busqueda.expandidos}")
    print(f"Nodos explorados: {busqueda.explorados}")
    tiempo = datetime.timedelta(seconds=busqueda.tiempoEjecucion)
    print(f"Duración de la ejecución: {tiempo}")
    coste = datetime.timedelta(seconds=busqueda.coste)
    print(f"Coste final: {coste}")
    reconstruirCamino(busqueda.solucion)

def reconstruirCamino(nodo):
    if nodo is None:
        return
    ids = [nodo.estado.identificador]
    while nodo.padre is not None:
        nodo = nodo.padre
        ids.append(nodo.estado.identificador)
    ids.reverse()
    print(f"Longitud de la solucion: {len(ids)}")
    print(f"Camino recorrido: {ids}")

def toMetersPerSecond(kilometersPerHour):
    return (kilometersPerHour * 1000) / 3600

def main():
    prob = Problema("examples_with_solutions/problems/huge/calle_agustina_aroca_albacete_5000_0.json")
    heur = Heuristica(prob.velocidad_maxima)
    print("Empezamos con BFS: \n")
    anchura = BFS(prob)
    anchura.start()
    imprimirResultado(anchura)
    #prob = Problema("examples_with_solutions/problems/small/calle_del_virrey_morcillo_albacete_250_3.json")
    print("\n---------------------------\n")
    print("Seguimos con DFS: \n")
    profundidad = DFS(prob)
    profundidad.start()
    imprimirResultado(profundidad)
    #prob = Problema("examples_with_solutions/problems/small/calle_del_virrey_morcillo_albacete_250_3.json")
    print("\n---------------------------\n")
    print("Continuamos con PM: ")
    primeroMejor = PM(prob, heur)
    primeroMejor.start()
    imprimirResultado(primeroMejor)
    #prob = Problema("examples_with_solutions/problems/small/calle_del_virrey_morcillo_albacete_250_3.json")
    print("\n---------------------------\n")
    print("Finalizamos con A*: ")
    aestrella = AE(prob, heur)
    aestrella.start()
    imprimirResultado(aestrella)

if __name__ == "__main__":
    main()

