import json

def loadData(fileName):
    if fileName.endswith(".json"):
        with open(fileName, 'r') as file:
            data = json.load(file)
        return data
    else:
        print("El fichero no es un .json")
        return

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
    data = loadData("problems/small/avenida_de_espanÌa_250_0.json")
    if not data:
        return
    intersecciones = []
    for element in data['intersections']:
        intersecciones.append(Interseccion(element['identifier'], element['longitude'], element['latitude']))
    

if __name__ == "__main__":
    main()