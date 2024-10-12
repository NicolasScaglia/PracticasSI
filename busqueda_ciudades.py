import json

def loadData(fileName):
    if not fileName.endswith(".json"):
        print("El archivo no es válido")
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

class Problema:


    def __init__(self, problemName):
        self.problemName = problemName
        data = loadData(self.problemName)
        if not data:
            return
        
        self.conexiones = {}
        self.acciones = []
        self.estados = {}
        # Diccionario de conexiones, id origen con posibles destinos
        self.conexiones = self.calcularConexiones(data)  
        # Diccionario de estados, id del estado, estado en el otro lado
        self.estados = self.calcularEstados(data)
        # Lista de todas las acciones posibles
        self.acciones = self.calcularAcciones(data)
        self.estadoFinal = self.estados[data['final']]
        self.estadoInicial = self.estados[data['initial']]
        
    def calcularConexiones(self, data):
        conexiones = {}
        for element in data['segments']:
            if element['origin'] not in conexiones:
                conexiones[element['origin']] = []
            conexiones[element['origin']].append(element['destination'])
        return conexiones
    
    def calcularAcciones(self, data):
        acciones = []
        for element in data['segments']:
            acciones.append(Accion(element['origin'], element['destination'], element['distance'], element['speed']))
        return acciones

    def calcularEstados(self, data):
        estados = {}
        for element in data['intersections']:
            estados[element['identifier']] = Estado(element['identifier'], element['longitude'], element['latitude'])
        return estados
  
class Busqueda:

    def __init__(self, problema):
        self.Problema = problema
        self.generados = 0
        self.expandidos = 0
        self.explorados = 0
        self.coste = 0
    
    def abrirNodo(self, nodo, frontera):
        self.expandidos += 1
        conexiones = self.Problema.conexiones[nodo.estado.identificador]
        for element in conexiones:
            accion = self.encontrarAccion(nodo.estado.identificador, element)
            nodoFrontera = Nodo(self.Problema.estados[element], nodo, accion)
            frontera.append(nodoFrontera)
            self.generados += 1

    def encontrarAccion(self, origen, destino):
        for element in self.Problema.acciones:
            if element.origen == origen and element.destino == destino:
                return element

    def esFinal(self, estado):
        return estado == self.Problema.estadoFinal

    def esVacia(self, frontera):
        if frontera:
            return False
        else:
            return True
        
class BusquedaA:

    def __init__(self, busqueda):
        self.Busqueda = busqueda
        self.frontera = []
        self.cerrados = set()
        self.nodoActual = Nodo(self.Busqueda.Problema.estadoInicial, None, None)
        self.Busqueda.abrirNodo(self.nodoActual, self.frontera)
        if self.Busqueda.esFinal(self.nodoActual.estado):
            self.solucion = self.nodoActual
            return
        self.solucion = self.algoritmoSimple()
        self.Busqueda.coste = self.solucion.coste

    def algoritmoSimple(self):
        while(True):
            if self.Busqueda.esVacia(self.frontera):
                return None
            self.nodoActual = self.borrarPrimero()
            if self.Busqueda.esFinal(self.nodoActual.estado):
                return self.nodoActual
            self.Busqueda.explorados += 1
            self.Explorar()
    
    def Explorar(self):
        if self.nodoActual.estado not in self.cerrados:
            self.cerrados.add(self.nodoActual.estado)
            self.Busqueda.abrirNodo(self.nodoActual, self.frontera)
    
    def borrarPrimero(self):
        return self.frontera.pop(0)
    
    def reconstruirCamino(self, nodo):
        ids = [nodo.estado.identificador]
        while nodo.padre is not None:
            nodo = nodo.padre
            ids.append(nodo.estado.identificador)
        print(f"Camino recorrido: {ids}")


    def imprimirResultado(self):
        print(f"Nodos generados: {self.Busqueda.generados}")
        print(f"Nodos expandidos: {self.Busqueda.expandidos}")
        print(f"Nodos explorados: {self.Busqueda.explorados}")
        print(f"Coste final: {self.Busqueda.coste}")
        self.reconstruirCamino(self.nodoActual)


def toMetersPerSecond(kilometersPerHour):
    return (kilometersPerHour * 1000) / 3600

def main():
    prob = Problema("problems/small/avenida_de_espanÌa_250_0.json")
    busqueda = Busqueda(prob)
    busquedaArboles = BusquedaA(busqueda)
    busquedaArboles.imprimirResultado()



if __name__ == "__main__":
    main()
    