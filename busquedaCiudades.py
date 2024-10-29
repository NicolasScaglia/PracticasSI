import json
from queue import PriorityQueue
import datetime
from geopy import distance

def loadData(fileName):
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
        self.data = loadData(self.problemName)
        if not self.data:
            return
        self.conexiones = {}
        self.acciones = {}
        self.estados = {}        
        # Diccionario de conexiones, id origen con posibles destinos
        self.conexiones = self.calcularConexiones()  
        # Diccionario de estados, id del estado, estado en el otro lado
        self.estados = self.calcularEstados()
        # Lista de todas las acciones posibles
        self.acciones = self.calcularAcciones()
        # Encontramos el estado final y el estado inicial en el diccionario de estados
        self.estadoFinal = self.estados[self.data['final']]
        self.estadoInicial = self.estados[self.data['initial']]
    
    def calcularConexiones(self):
        conexiones = {}
        for element in self.data['segments']:
            if element['origin'] not in conexiones:
                conexiones[element['origin']] = []
            conexiones[element['origin']].append(element['destination'])
        return conexiones
    
    def calcularAcciones(self):
        acciones = {}
        for element in self.data['segments']:
            if element['origin'] not in acciones:
                acciones[element['origin']] = []
            acciones[element['origin']].append(Accion(element['origin'], element['destination'], element['distance'], element['speed']))
        return acciones
    
    def calcularEstados(self):
        estados = {}
        for element in self.data['intersections']:
            estados[element['identifier']] = Estado(element['identifier'], element['longitude'], element['latitude'])
        return estados
    
class Heuristica(Problema):
    def __init__(self, problemName):
        super().__init__(problemName)
        self.posicionFinal = (self.estadoFinal.latitud, self.estadoFinal.longitud)
        self.heuristica = self.calcularHeuristica()

    def calcularHeuristica(self):
        velocidadMax = 0
        for element in self.data['segments']:
            if element['speed'] > velocidadMax:
                velocidadMax = element['speed']
        return toMetersPerSecond(velocidadMax)
    
    def funcionHeuristica(self, longitud, latitud):
        posicionActual = (latitud, longitud)
        return distance.distance(self.posicionFinal, posicionActual).m / self.heuristica

class Busqueda(Heuristica):

    frontera = []
    cerrados = set()
    nodoActual = Nodo(None, None, None)
    generados = 0
    expandidos = 0
    explorados = 0
    coste = 0

    def __init__(self, problemName):
        super().__init__(problemName)
        self.nodoActual = Nodo(self.estadoInicial, None, None)
        self.abrirNodo()
        if self.esFinal():
            self.solucion = self.nodoActual
            return
        self.solucion = self.Algoritmo()
        if self.solucion is not None:
            self.coste = self.solucion.coste

    def encontrarAccion(self, destino):
        for element in self.acciones[self.nodoActual.estado.identificador]:
            if element.destino == destino:
                return element
        print("No se han podido encontrar acciones.")
        return None

    def esFinal(self):
        return self.nodoActual.estado == self.estadoFinal
    
    def esVacia(self):
        return not self.frontera
    
    def abrirNodo(self):
        if self.nodoActual.estado.identificador in self.conexiones:
            conexiones = self.conexiones[self.nodoActual.estado.identificador]
        else:
            return
        self.expandidos += 1
        for element in conexiones:
            accion = self.encontrarAccion(element)
            nodoFrontera = Nodo(self.estados[element], self.nodoActual, accion)
            self.frontera.append(nodoFrontera)
            self.generados += 1

    def Algoritmo(self):
        while(True):
            if self.esVacia():
                print("[INFO] No se ha encontrado solución\n")
                return self.nodoActual
            self.nodoActual = self.sacarSiguiente()
            if self.esFinal():
                return self.nodoActual
            self.explorados += 1
            self.Explorar()
    
    def Explorar(self):
        if self.nodoActual.estado not in self.cerrados:
            self.cerrados.add(self.nodoActual.estado)
            self.abrirNodo()
    
    def sacarSiguiente(self):
        NotImplemented
    
class BFS(Busqueda):

    def sacarSiguiente(self):
        return self.frontera.pop(0)
    
class DFS(Busqueda):

    def sacarSiguiente(self):
        return self.frontera.pop(len(self.frontera) - 1)



class PM(Busqueda):

    frontera = PriorityQueue() 

    def abrirNodo(self):
        self.expandidos += 1
        if self.nodoActual.estado.identificador in self.conexiones:
            conexiones = self.conexiones[self.nodoActual.estado.identificador]
        else:
            return
        conexiones.sort()
        for element in conexiones:
            accion = self.encontrarAccion(element)
            nodoFrontera = Nodo(self.estados[element], self.nodoActual, accion)
            self.frontera.put((self.funcionHeuristica(nodoFrontera.estado.longitud, nodoFrontera.estado.latitud), nodoFrontera))
            self.generados += 1
    
    def sacarSiguiente(self):
        return self.frontera.get()[1]
    
class AE(Busqueda):

    frontera = PriorityQueue() 

    def abrirNodo(self):
        self.expandidos += 1
        if self.nodoActual.estado.identificador in self.conexiones:
            conexiones = self.conexiones[self.nodoActual.estado.identificador]
        else:
            return
        conexiones.sort()
        for element in conexiones:
            accion = self.encontrarAccion(element)
            nodoFrontera = Nodo(self.estados[element], self.nodoActual, accion)
            # Calculamos el valor f (coste + heurística)
            f = nodoFrontera.coste + self.funcionHeuristica(nodoFrontera.estado.longitud, nodoFrontera.estado.latitud)
            self.frontera.put((f, nodoFrontera))
            self.generados += 1

    def sacarSiguiente(self):
        return self.frontera.get()[1]

def imprimirResultado(busqueda):
    print(f"Nodos generados: {busqueda.generados}")
    print(f"Nodos expandidos: {busqueda.expandidos}")
    print(f"Nodos explorados: {busqueda.explorados}")
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
    print(f"Camino recorrido: {ids}")

def toMetersPerSecond(kilometersPerHour):
    return (kilometersPerHour * 1000) / 3600

def main():
    print("Empezamos con BFS: \n")
    anchura = BFS("examples_with_solutions/problems/huge/calle_agustina_aroca_albacete_5000_0.json")
    imprimirResultado(anchura)
    print("\n---------------------------\n")
    print("Seguimos con DFS: \n")
    profundidad = DFS("examples_with_solutions/problems/huge/calle_agustina_aroca_albacete_5000_0.json")
    imprimirResultado(profundidad)
    print("\n---------------------------\n")
    print("Continuamos con PM: ")
    primeroMejor = PM("examples_with_solutions/problems/huge/calle_agustina_aroca_albacete_5000_0.json")
    imprimirResultado(primeroMejor)
    print("\n---------------------------\n")
    print("Finalizamos con A*: ")
    aestrella = AE("examples_with_solutions/problems/huge/calle_agustina_aroca_albacete_5000_0.json")
    imprimirResultado(aestrella)

if __name__ == "__main__":
    main()

