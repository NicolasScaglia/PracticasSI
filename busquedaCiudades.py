import json

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

class HEstado:
    def __init__(self, heur):
        self.heuristica = heur

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

class Problema:
    def __init__(self, problemName):
        self.problemName = problemName
        self.data = loadData(self.problemName)
        if not self.data:
            return
        self.conexiones = {}
        self.acciones = []
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
        acciones = []
        for element in self.data['segments']:
            acciones.append(Accion(element['origin'], element['destination'], element['distance'], element['speed']))
        return acciones
    
    def calcularEstados(self):
        estados = {}
        for element in self.data['intersections']:
            estados[element['identifier']] = Estado(element['identifier'], element['longitude'], element['latitude'])
        return estados
    
class HProblema(Problema):
    def __init__(self):
        self.heuristica = self.calcularHeuristica()
        self.hestados = self.calcularHEstados()
        self.hestadoFinal = HEstado(self.estadoFinal, 0)
        self.hestadoInicial = HEstado(self.estadoInicial, self.funcionHeuristica(self.estadoInicial['longitude'], self.estadoInicial['latitude']))

class Busqueda(Problema):

    def __init__(self, problemName):
        super().__init__(problemName)
        self.frontera = []
        self.cerrados = set()
        self.nodoActual = Nodo(self.estadoInicial, None, None)
        self.generados = 0
        self.expandidos = 0
        self.explorados = 0
        self.coste = 0
        self.abrirNodo()
        if self.esFinal():
            self.solucion = self.nodoActual
            return
        self.solucion = self.Algoritmo()
        if self.solucion is not None:
            self.coste = self.solucion.coste

    def encontrarAccion(self, origen, destino):
        for element in self.acciones:
            if element.origen == origen and element.destino == destino:
                return element
        print("No se han podido encontrar acciones.")
        return None

    def esFinal(self):
        return self.nodoActual.estado == self.estadoFinal
    
    def esVacia(self):
        return not self.frontera
    
    def abrirNodo(self):
        self.expandidos += 1
        if self.nodoActual.estado.identificador in self.conexiones:
            conexiones = self.conexiones[self.nodoActual.estado.identificador]
        else:
            return
        conexiones.sort()
        for element in conexiones:
            accion = self.encontrarAccion(self.nodoActual.estado.identificador, element)
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

def imprimirResultado(busqueda):
    print(f"Nodos generados: {busqueda.generados}")
    print(f"Nodos expandidos: {busqueda.expandidos}")
    print(f"Nodos explorados: {busqueda.explorados}")
    print(f"Coste final: {busqueda.coste}")
    reconstruirCamino(busqueda.solucion)

def reconstruirCamino(nodo):
    if nodo is None:
        return
    ids = [nodo.estado.identificador]
    while nodo.padre is not None:
        nodo = nodo.padre
        ids.append(nodo.estado.identificador)
    print(f"Camino recorrido: {ids}")

def toMetersPerSecond(kilometersPerHour):
    return (kilometersPerHour * 1000) / 3600

def main():
    print("Empezamos con BFS: \n")
    anchura = BFS("problems/small/avenida_de_espanÌa_250_0.json")
    imprimirResultado(anchura)
    print("\n---------------------------\n")
    print("Seguimos con DFS: \n")
    profundidad = DFS("problems/small/avenida_de_espanÌa_250_0.json")
    imprimirResultado(profundidad)

if __name__ == "__main__":
    main()

