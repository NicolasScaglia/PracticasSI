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
        if self.padre is not None:
            self.profundiad = self.padre.profundidad + 1
            self.coste = self.padre.coste + self.accion.coste
        else:
            self.profundiad = 0
            self.coste = 0

class Problema:


    def __init__(self, problemName):
        self.problemName = problemName
        data = loadData(self.problemName)
        if not data:
            return
        # Diccionario de conexiones, id origen con posibles destinos
        self.conexiones = self.calcularConexiones(data)  
        # Diccionario de estados, id del estado, estado en el otro lado
        self.estados = self.calcularEstados(data)
        # Lista de todas las acciones posibles
        self.acciones = self.calcularAcciones(data)
        self.estadoFinal = Estado(data['final']['identifier'], data['final']['longitude'], data['final']['latitude'])
        self.estadoInicial = Estado(data['initial']['identifier'], data['initial']['longitude'],data['initial']['latitude'])
        
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
        self.frontera = []
        self.cerrados = set()
        self.nodoActual = Nodo(self.Problema.estadoInicial, None, None)
    
    def abrirNodo(self, id):
        self.expandidos = self.expandidos + 1
        conexiones = self.conexiones[id]
        for elemento in conexiones:
            self.frontera.append(elemento)
            self.generados = self.generados + 1

    def encontrarAccion(self, origen, destino):
        for elemento in self.Problema.acciones:
            if elemento['origin'] == origen and elemento['destination'] == destino:
                return elemento

    def borrarPrimero(self):
        self.frontera.pop(0)

    def Explorar(self):
        if self.nodoActual.estado not in self.cerrados:
            self.cerrados.Add(self.nodoActual.estado)
            self.abrirNodo(self.nodoActual.estado.identificador)

    def algoritmo_simple(self):
        while(True):
            if self.Vacia():
                return None
            proximo = self.frontera.pop(0)
            actual = self.nodoActual.estado.identificador
            self.nodoActual = Nodo(proximo, self.nodoActual, self.encontrarAccion(actual, proximo.identificador))
            self.explorados = self.explorados + 1
            if self.esFinal(self.nodoActual.estado):
                return self.nodoActual
            self.Explorar()

    def esFinal(self, estado):
        return estado == self.Problema.estadoFinal

    def Vacia(self):
        return self.frontera.count()
    
    

def toMetersPerSecond(kilometersPerHour):
    return (kilometersPerHour * 1000) / 3600

def main():
    prob = Problema()
    
    

if __name__ == "__main__":
    main()