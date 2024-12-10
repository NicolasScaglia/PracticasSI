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
        self.num_estaciones = self.data['number_stations']
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
        # self.velocaidad_media = 0
        self.velocidad_maxima = 0
        # cuenta = 0
        self.data['segments'].sort(key = lambda a : a['destination'])
        for element in self.data['segments']:
            if element['origin'] not in self.acciones:
                self.acciones[element['origin']] = []
            self.acciones[element['origin']].append(Accion(element['origin'], element['destination'], element['distance'], element['speed']))
            if element['speed'] > self.velocidad_maxima:
                self.velocidad_maxima = element['speed']
        # self.velocaidad_media /= cuenta
        
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
        nodoInicial = Nodo(self.problema.estado_inicial, None, None)
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
        return not self.frontera.empty()
    
    @abstractmethod
    def sacar_siguiente(self):
        pass    

    def es_final(self):
        return self.nodoActual.estado == self.problema.estado_final

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

class AE(Busqueda):

    def __init__(self, problema, heuristica):
        frontera = PriorityQueue()
        super().__init__(problema, frontera)
        self.heuristica = heuristica

    def insertar(self, nodo):
        posicion_actual = (nodo.estado.latitud, nodo.estado.longitud)
        prioridad = self.heuristica.funcion_heuristica(posicion_actual, (self.problema.estado_final.latitud, self.problema.estado_final.longitud)) + nodo.coste
        self.frontera.put((prioridad, nodo))
        
    def sacar_siguiente(self):
        return self.frontera.get()[1]

def limitar_seleccionados(cadena, seleccionados):
    if cadena.count(1) == seleccionados:
        return cadena;
    elif cadena.count(1) > seleccionados:
        indices = [i for i, bit in enumerate(cadena) if bit == 1]
        exceso = len(indices) - seleccionados
        cambios = random.sample(indices, exceso)
        for i in cambios:
            cadena[i] = 0
        return cadena
    else:
        indices = [i for i, bit in enumerate(cadena) if bit == 0]
        faltantes = seleccionados - cadena.count(1)
        cambios = random.sample(indices, faltantes)
        for i in cambios:
            cadena[i] = 1
        return cadena
            
class Individuo():

    # Cadena genética representa la solución del individuo.
    # Tamaño representa el tamaño de la cadena genética.
    # Todo individuo tiene un valor de fitness, o lo que es lo mismo,
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
        sumPop = 0
        min = -112
        for element in problema.candidatos:
            for i in range(0, len(self.cadena_genetica)):
                if self.cadena_genetica[i] == 1:
                    problema.set_estado_inicial(problema.estados[element[0]])
                    problema.set_estado_final(problema.estados[problema.candidatos[i][0]])
                    estrella = AE(problema, Heuristica(problema.velocidad_maxima))
                    estrella.start()
                    if estrella.solucion.coste * element[1] < min or min < 0:
                        min = estrella.solucion.coste * element[1]
            sumPop += element[1]
        self.fitness = (1/sumPop) * min

    # Función mutable
    def cruzar(self, otro, seleccionados=1):

        cruce = random.randint(1, len(self.cadenaG) - 1)

        hijo1 = otro.cadena_genetica[cruce:] + self.cadena_genetica[:cruce]
        hijo2 = self.cadena_genetica[cruce:] + otro.cadena_genetica[:cruce]

        hijo1 = limitar_seleccionados(hijo1, seleccionados)
        hijo2 = limitar_seleccionados(hijo2, seleccionados)

        return hijo1, hijo2

    def mutar(self, seleccionados=1):
        pass

    
    def generar(self):
        # Mientras que no haya el número de 1s (seleccionados) igual a
        # el número de seleccionados que necesitamos, continuamos.
        while self.cadena_genetica.count(1) != self.seleccionados:
            pos = random.randint(0, len(self.cadena_genetica) - 1)
            self.cadena_genetica[pos] = 1

    def __eq__(self, otro):
        return self.cadena_genetica.__eq__(otro.cadena_genetica)


class AlgoritmoAleatorio():


    # Se debe pasar el problema en concreto y el tamaño de la población
    # al algoritmo.
    def __init__(self, problema, tamano_poblacion = 100):
        self.problema = problema
        self.tamano_poblacion = tamano_poblacion

        # Utilizamos una caché para que si ya tenemos un resultado, no volver
        # a realizar una evaluación innecesaria. Key = cadena_genetica ,
        # Value = fitness 
        # TODO buscar mejor clave para la caché.
        self.cache = {}
    
    def algoritmo(self):
        mejor_individuo = None
        contadorOptimoLocal = 0

        # Comprobamos que hayamos alcanzado al menos un óptimo local
        # (las últimas tres soluciones sean iguales)

        # Inicializamos el mejor individuo local a nulo en cada iteración.
        mejor_individuo_local = None

        # Hacemos un bucle que dure el tamaño de la población.
        for i in range(self.tamano_poblacion):

            # Generamos el individuo en el momento en vez de guardarlo en un array, así
            # ahorramos memoria.
            temp = Individuo(tamano=len(self.problema.candidatos), seleccionados=self.problema.num_estaciones)

            # Variable fitness temporal.
            fitness = 0

            # Acceso a la caché (simplifica la lectura del código).
            acceso = "".join(map(str, temp.cadena_genetica))

            # Si existe valor en caché, usamos ese y no evaluamos de nuevo.
            if acceso in self.cache and self.cache[acceso] is not None:
                fitness = self.cache[acceso]
            else:
                # Si no, fitness será el valor de la evaluación y la guardamos en caché.
                temp.evaluar(self.problema)
                fitness = temp.fitness
                self.cache[acceso] = fitness

            # Actualizamos el mejor valor.
            if mejor_individuo_local is None:
                mejor_individuo_local = temp
            
            if mejor_individuo_local.fitness < fitness:
                mejor_individuo_local = temp
                
            #     # Devolvemos el mejor individuo.
            # if mejor_individuo is None:
            #     mejor_individuo = mejor_individuo_local
            # elif mejor_individuo_local.fitness > mejor_individuo.fitness:
            #     mejor_individuo = mejor_individuo_local
            # elif mejor_individuo_local.__eq__(mejor_individuo):
            #     contadorOptimoLocal += 1

        return mejor_individuo_local


# def imprimirResultado(busqueda):
#     print(f"Nodos generados: {busqueda.generados}")
#     print(f"Nodos expandidos: {busqueda.expandidos}")
#     print(f"Nodos explorados: {busqueda.explorados}")
#     tiempo = datetime.timedelta(seconds=busqueda.tiempoEjecucion)
#     print(f"Duración de la ejecución: {tiempo}")
#     coste = datetime.timedelta(seconds=busqueda.coste)
#     print(f"Coste final: {coste}")
#     reconstruirCamino(busqueda.solucion)

# # def reconstruirCamino(nodo):
# #     if nodo is None:
# #         return
# #     ids = [nodo.estado.identificador]
# #     while nodo.padre is not None:
# #         nodo = nodo.padre
# #         ids.append(nodo.estado.identificador)
# #     ids.reverse()
# #     print(f"Longitud de la solucion: {len(ids)}")
# #     print(f"Camino recorrido: {ids}")

def imprimir_solucion(solucion, candidatos):

    aux = []
    for i in range(len(solucion)):
        if solucion[i] == 1:
            aux.insert(0, candidatos[i][0])
    print(aux)

def toMetersPerSecond(kilometersPerHour):
    return (kilometersPerHour * 1000) / 3600

def main():
    prob = Problema("M:\\University\\PracticasSI\\P2_SI\\sample-problems-lab2\\toy\\calle_del_virrey_morcillo_albacete_250_3_candidates_15_ns_4.json")
    AA = AlgoritmoAleatorio(prob, 100)
    solucionAA = AA.algoritmo()
    imprimir_solucion(solucionAA.cadena_genetica, prob.candidatos)

if __name__ == "__main__":
    main()