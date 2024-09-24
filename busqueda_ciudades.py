import json

def loadData(fileName):
    if fileName.endswith(".json"):
        with open(fileName, 'r') as file:
            data = json.load(file)
        return data
    else:
        print("El fichero no es un .json")
        return


#class Ubicacion:

#class Interseccion:

#class MoverseAInterseccion:

#class ElegirInterseccion:

def toMetersPerSecond(kilometersPerHour):
    return (kilometersPerHour * 1000) / 3600

def main():
    data = loadData("problems/small/avenida_de_espanÌa_250_0.json")
    if not data:
        return
    print(data['address'])

if __name__ == "__main__":
    main()