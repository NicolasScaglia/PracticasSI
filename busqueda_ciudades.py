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

    def __init__(self, est, pad, acc, prof, cost):
        self.estado = est
        self.padre = pad
        self.accion = acc
        self.profundiad = prof
        self.coste = cost

class Problema:


    def __init__(self, problemName):
        self.problemName = problemName
        data = loadData(self.problemName)
        if not data:
            return
        self.conexiones = self.calcularAcciones(data)

    def calcularAcciones(self, data):
        conexiones = {}
        for elements in data['segments']:
            if elements['origin'] not in conexiones:
                conexiones[elements['origin']] = []
            conexiones[elements['origin']].append(elements['destination'])
        return conexiones
    
    

def toMetersPerSecond(kilometersPerHour):
    return (kilometersPerHour * 1000) / 3600

class Interseccion:

    def __init__(self, id, long, lat):
        self.identificacion = id
        self.longitud = long
        self.latitud = lat

class Seccion:

    def __init__(self, origen, dest, dist, vel):
        self.origen = origen
        self.destino = dest
        self.peso = dist / toMetersPerSecond(vel)



def main():
    prob = Problema()
    
    

if __name__ == "__main__":
    main()