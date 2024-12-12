import json
from queue import PriorityQueue
from geopy import distance
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
        self.candidatos = self.data['candidates']
        self.numero_estaciones = self.data['number_stations']
    
    # Diccionario de acciones para calcular las conexiones entre intersecciones
    def calcular_acciones(self):
        self.acciones = {}
        self.velocidad_maxima = 0
        self.data['segments'].sort()
        for element in self.data['segments']:
            if element['origin'] not in self.acciones:
                self.acciones[element['origin']].put((element['destination'],Accion(element['origin'], element['destination'], element['distance'], element['speed'])))
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
    
    def funcion_heuristica(self, posicionActual, posicionFinal):
        return distance.distance(posicionActual, posicionFinal).m / toMetersPerSecond(self.heuristica)

class Busqueda(ABC):

    
    def __init__(self, problema, frontera):
        self.problema = problema
        self.frontera = frontera

    def start(self):
        self.solucion = self.algoritmo()
        
    def algoritmo(self):
        self.cerrados = set()
        nodoInicial = Nodo(self.problema.estadoInicial, None, None)
        self.insertar(nodoInicial)
        while(True):
            if self.es_vacia():
                self.nodoActual.coste = 3600*5
                return self.nodoActual.coste
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
        return self.nodoActual.estado == self.problema.estadoFinal

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
        posicion_actual = (nodo.estado.latitud, nodo.estado.longitud)
        prioridad = self.heuristica.funcion_heuristica_geodesica(posicion_actual, self.problema.posicionFinal) + nodo.coste
        self.frontera.put((prioridad, nodo))

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
    prob = Problema("sample-problems-lab2/toy/calle_del_virrey_morcillo_albacete_250_3_candidates_15_ns_4.json")

if __name__ == "__main__":
    main()

