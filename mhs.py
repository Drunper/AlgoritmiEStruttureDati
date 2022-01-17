# -*- coding: utf-8 -*-
"""
Created on Mon Jan 7 11:07:53 2022

@author: patri
"""

import re, linecache, sys, os, copy
import queue, array as arr
from collections import deque
from time import process_time
from argparse import ArgumentParser, RawTextHelpFormatter
from memory_profiler import memory_usage
from pynput import keyboard
import matplotlib.pyplot as plt

comandi_disponibili = ("run", "track", "plot")
messaggio_help = """
Utilizzo: mhs <comando> <opzioni> <input>
Comandi disponibili:

    run      calcola i MHS della matrice in ingresso, fornendo in output informazioni sull'esecuzione
    track    applica l'algoritmo sulla matrice in ingresso, tracciando l'uso della memoria
    plot     rappresenta graficamente i risultati ottenuti dall'applicazione del comando track

Per informazioni più specifiche scrivi mhs <comando> --help
"""

termina_esecuzione = False
def on_press(key):
    global termina_esecuzione
    if key == keyboard.Key.space:
        print ("Esecuzione terminata dall'utente")
        termina_esecuzione = True
        return False

def read_mat(file): 
  data=[]
  for line in file:
    if line[0]!=";":
      newLine= line.replace("-","")
      l= newLine.split(" ")
      l.remove("\n")     
      data.append(arr.array('B', list(map(int, l))))
  file.close
  return data

def array_dominio(nFile):
  line = linecache.getline(nFile, 5)
  dom=re.findall('\(([^)]+)', line)
  array = list(dom)
  return array  

def leggi_matrice(percorso_file):
  f= open(percorso_file,"r")
  array_matrice = read_mat(f)
  print("------- array originale dim: ----")
  print(len(array_matrice), len(array_matrice[0]))
  arrayDominio = array_dominio(percorso_file)
  dominioBase = list(arrayDominio)
  print("Verifica dimensioni:")
  if len(array_matrice[0]) == len(dominioBase):
    print("OK DIMENSIONI COINCIDONO !!")
  else: 
    print("ERRORE SU DIMENSIONI FILE !!")
    sys.exit(1)
  print("-------array dom originale: ----")
  print("Len dom: " + str(len(dominioBase)))

  dominio_base = list(range(0, len(array_matrice[0])))
  return array_matrice, dominio_base, len(array_matrice), len(array_matrice[0])

def succ(elem): 
  if elem == -1: 
    return 1
  else:
    return elem + 1

def max_insieme(insieme):
  if not insieme: 
    return -1
  else: 
    return insieme[-1]

def alg_base(A, dominio, colonne_originali):
  global termina_esecuzione
  start_time=process_time()
  lista_mhs=[]  
  queue=deque()
  valore_max = len(A[0]) 
  queue.append(arr.array('I', []))
  vett_rapp = arr.array('I', [0] * len(A))
  with keyboard.Listener(on_press=on_press) as listener:
    while queue and not termina_esecuzione:
      insieme = queue.popleft()
      e = succ(max_insieme(insieme))
    
      for elem in range(e,valore_max+1):
        nuovo_insieme = insieme.tolist() 
        nuovo_insieme.append(elem)
        nuovo_insieme = arr.array('I', nuovo_insieme) 
        crea_vett_rapp(nuovo_insieme, vett_rapp, A)     
        result = check(nuovo_insieme, vett_rapp)
        if result == "ok" and elem != valore_max:
          queue.append(nuovo_insieme)    
        elif result == "mhs":
          lista_mhs.append(output(nuovo_insieme, dominio, colonne_originali))
  return lista_mhs, process_time() - start_time

def check(nuovo_insieme, vettore):
  proiezione= set(vettore) 
  for i in nuovo_insieme:
    if i not in proiezione:
      return "ko" 
 
  if 0 in proiezione:
    return "ok"
  else:
    return "mhs"  

def crea_vett_rapp(insieme, vett_rapp, A): 
  for i in range(len(A)):
    vett_rapp[i] = 0
    for j in insieme:
      if A[i][j-1]:
        if vett_rapp[i]:
          vett_rapp[i] = 65535 
          break
        else:
          vett_rapp[i] = j

def output(mhs, dominio, colonne_originali): 
    l = [0] * colonne_originali
    for elem in mhs:
        l[dominio[elem - 1]] = 1
    return arr.array('B', l)

def contiene(A, first, second): # funzione che mi dice se la prima riga contiene la seconda
  for k in range(0, len(A[0])):
    if (not A[first][k]) and A[second][k]:
      return False
  return True

def costruisci_lista(A): 
  l = []
  for i in range(0, len(A)):
    l.append((sum(A[i]), i))  
  l.sort(key=lambda x: x[0], reverse=True) 
  return list(list(zip(*l))[1])

def togli_righe(A): # Lavora in-place sulla matrice A
  prio_queue = queue.PriorityQueue()
  l = costruisci_lista(A)
  j = len(l)
  for i in range(j):
    for k in range(i+1, j):
      if contiene(A, l[i], l[k]):
        prio_queue.put((j - l[i]))
        break

  l = []
  while not prio_queue.empty():
    x = prio_queue.get()
    ind = j - x
    l.append(ind)
    del A[ind]
  return l, len(l) # restituisce gli indici di righe rimosse e il numero complessivo

def colonna_di_zeri(A, i):
  for j in range(len(A)):
    if A[j][i]:
      return False
  return True

def resize_dom_array(dom,indiciDaTogliere):
  new_dom = dom.copy() #Fatto per poter testare la funzione ripetutamente
  if indiciDaTogliere:
    for i in range(len(indiciDaTogliere)-1,-1,-1):  
      del new_dom[indiciDaTogliere[i]]
  return new_dom 

def togli_colonne(A):
  l = []
  for i in range(len(A[0])):
    if colonna_di_zeri(A, i):
      l.append(i)
  for i in reversed(l):
    deque(map(lambda x: x.pop(i), A), maxlen=0)
  return l, len(l) # Indici rimossi e il numero complessivo

def alg_con_pre(A, dominio, colonne_originali):
  B = copy.deepcopy(A)  # Aggiunta per poter eseguire l'algoritmo più volte senza dover leggere nuovamente la matrice
  indici_righe_rimosse, numero_righe_rimosse = togli_righe(B)
  indici_colonne_rimosse, numero_colonne_rimosse = togli_colonne(B)
  dominio_pre_elaborato = resize_dom_array(dominio, indici_colonne_rimosse)
  matrice_mhs, tempo_di_esecuzione_base = alg_base(B, dominio_pre_elaborato, colonne_originali)
  return matrice_mhs, tempo_di_esecuzione_base, numero_righe_rimosse, numero_colonne_rimosse, indici_righe_rimosse, indici_colonne_rimosse

def max_min_mhs(matrice_mhs):
    return sum(max(matrice_mhs, key=sum)), sum(min(matrice_mhs, key=sum))

def stringa_da_array(array):
    if array:
        stringa = str(array[0])
        for elem in array[1:]:
            stringa = stringa + " " + str(elem)
        stringa = stringa + " " + "-\n"
        return stringa
    else:
        return '\n'
    
def scrivi_risultati(nome_file, nome_matrice, numero_righe, numero_colonne, 
                     esecuzione_terminata, mhs_trovati, cardinalità_minima, cardinalità_massima, 
                     tempo_di_esecuzione_base, matrice_mhs, pre_elaborazione, righe_rimosse=None, colonne_rimosse=None, 
                     indici_righe=None, indici_colonne=None):
    with open(nome_file, 'w') as output_file:
        if pre_elaborazione:
            output_file.write('Report esecuzione algoritmo con pre-elaborazione\n')
        else:
            output_file.write('Report esecuzione algoritmo base\n')
        output_file.write('Nome matrice: {}\n'.format(nome_matrice))
        output_file.write('Numero righe: {}\n'.format(numero_righe))
        output_file.write('Numero colonne: {}\n'.format(numero_colonne))
        output_file.write('\n')
        
        if pre_elaborazione:
            output_file.write('Pre-elaborazione\n')
            output_file.write('Righe rimosse: {}\n'.format(righe_rimosse))
            output_file.write('Colonne rimosse: {}\n'.format(colonne_rimosse))
            output_file.write('Indici righe rimosse:\n')
            output_file.write(stringa_da_array(indici_righe))
            output_file.write('Indici colonne rimosse:\n')
            output_file.write(stringa_da_array(indici_colonne))
            output_file.write('\n')
        
        if esecuzione_terminata:
            output_file.write('Esecuzione: terminata\n')
        else:
            output_file.write('Esecuzione: non terminata\n')
        output_file.write('Numero MHS trovati: {}\n'.format(mhs_trovati))
        output_file.write('Cardinalità minima MHS: {}\n'.format(cardinalità_minima))
        output_file.write('Cardinalità massima MHS: {}\n'.format(cardinalità_massima))
        
        output_file.write('\n')
        output_file.write('Tempo medio di esecuzione algoritmo: {}\n'.format(tempo_di_esecuzione_base))
                
     
    mhs_file = ""
    if pre_elaborazione:
        mhs_file = 'MHS_p_' + nome_matrice + '.txt'
    else:
        mhs_file = 'MHS_' + nome_matrice + '.txt'
    with open(mhs_file, 'w') as output_file:
        output_file.write('MHS trovati:\n')
        for mhs in matrice_mhs:
            output_file.write(stringa_da_array(mhs))

def plot_memoria(mem_usata, timestamps, titolo, nome_file, mostra_plot=False):
  fig = plt.figure(figsize=(10, 6), dpi=90)
  ax = fig.add_subplot(111)
  ax.set_title(titolo, fontsize=14)
  global_start = float(timestamps[0])
  time = [i - global_start for i in timestamps]
  ax.plot(time, mem_usata, 'r')
  ax.spines['top'].set_color("none")
  ax.spines['right'].set_color("none")
  ax.set_xlabel("tempo (in secondi)", fontsize=12)
  ax.set_ylabel("memoria usata (in MiB)", fontsize=12)
  plt.savefig(nome_file)
  if mostra_plot:
    plt.show()
    
def read_mem_usata(nome_file):
    mem_usata = []
    timestamps = []
    with open(nome_file, 'r') as track_file:
        next(track_file)
        for l in track_file:
            mem, timestamp = l.split(' ')
            mem_usata.append(float(mem))
            timestamps.append(float(timestamp))
    return mem_usata, timestamps

def seleziona_comando():
    if len(sys.argv) <= 1:
        print(messaggio_help)
        sys.exit(1)
    if not sys.argv[1] in comandi_disponibili:
        print(messaggio_help)
        sys.exit(1)
    return sys.argv.pop(1)

def run():
    parser = ArgumentParser(usage="mhs run [opzioni] matrix", formatter_class=RawTextHelpFormatter)
    parser.add_argument("-p", "--preelaborazione", dest="pre_elaborazione", action="store_true",
                        help="""Effettua la pre-elaborazione (rimozione righe e colonne) della matrice prima di applicare l'algoritmo""")
    parser.add_argument("-o", "--output", dest="output",                       
                        help="""Nome del file in cui verrà salvato il report riguardante l'esecuzione dell'algoritmo sulla matrice di input""")
    parser.add_argument("matrix",
                        help="""Nome del file che contiene la matrice di input"""
                        )
    args = parser.parse_args()
    
    if not os.path.isfile(args.matrix):
        print("Il percorso specificato non è un file")
        sys.exit(1)
    nome_matrice = os.path.splitext(args.matrix)[0]
    
    if args.output:
        output = args.output
    elif args.pre_elaborazione:
        output = "Risultati_p_" + nome_matrice + ".txt"
    else:
        output = "Risultati_" + nome_matrice + ".txt"
    
    array_matrice, dominio_base, righe, colonne = leggi_matrice(args.matrix)
    
    if args.pre_elaborazione:
        matrice_mhs, tempo_di_esecuzione_base, righe_rimosse, colonne_rimosse, indici_righe, indici_colonne = alg_con_pre(array_matrice, dominio_base, colonne)
        mhs_trovati = len(matrice_mhs)
        max_mhs, min_mhs = max_min_mhs(matrice_mhs)
    else:
        matrice_mhs, tempo_di_esecuzione_base = alg_base(array_matrice, dominio_base, colonne)
        mhs_trovati = len(matrice_mhs)
        max_mhs, min_mhs = max_min_mhs(matrice_mhs)
    
    if args.pre_elaborazione:
        scrivi_risultati(output, nome_matrice, righe, colonne, not termina_esecuzione, mhs_trovati, min_mhs, max_mhs, tempo_di_esecuzione_base, matrice_mhs, True, righe_rimosse, colonne_rimosse, 
                         indici_righe, indici_colonne)
    else:
        scrivi_risultati(output, nome_matrice, righe, colonne, not termina_esecuzione, mhs_trovati, min_mhs, max_mhs, tempo_di_esecuzione_base, matrice_mhs, False)
    
def track():
    parser = ArgumentParser(usage="mhs track [opzioni] matrix", formatter_class=RawTextHelpFormatter)
    parser.add_argument("-p", "--preelaborazione", dest="pre_elaborazione", action="store_true",
                        help="""Effettua la pre-elaborazione (rimozione righe e colonne) della matrice prima di applicare l'algoritmo""")
    parser.add_argument("-o", "--output", dest="output",                       
                        help="""Nome del file in cui verrà salvato il consumo di memoria nel tempo""")
    parser.add_argument("matrix",
                        help="""Nome del file che contiene la matrice di input"""
                        )
    args = parser.parse_args()
    
    if not os.path.isfile(args.matrix):
        print("Il percorso specificato non è un file")
        sys.exit(1)
    nome_matrice = os.path.splitext(args.matrix)[0]
    
    if args.output:
        output = args.output
    elif args.pre_elaborazione:
        output = "Track_mem_p_" + nome_matrice + ".txt"
    else:
        output = "Track_mem_" + nome_matrice + ".txt"
    
    array_matrice, dominio_base, righe, colonne = leggi_matrice(args.matrix)

    if args.pre_elaborazione:
        mem_usage = memory_usage(proc=(alg_con_pre, (array_matrice, dominio_base, colonne),), timestamps=True)
    else:
        mem_usage = memory_usage(proc=(alg_base, (array_matrice, dominio_base, colonne)), timestamps=True)  
    with open(output, "w") as f:
        f.write("Nome matrice: {}\n".format(nome_matrice))
        for mem, timestamp in mem_usage:
            f.write("{0:.6f} {1:.4f}\n".format(mem, timestamp))
    
def plot():    
    parser = ArgumentParser(usage="mhs plot [opzioni] traccia", formatter_class=RawTextHelpFormatter)
    parser.add_argument("-s", "--show", dest="show", default=False, action="store_true",
                        help="""Mostra il plot dopo averlo disegnato""")
    parser.add_argument("-t", "--titolo", dest="titolo",
                        help="""Titolo del plot""")
    parser.add_argument("-o", "--output", dest="output",                       
                        help="""Nome del file in cui verrà salvato il plot""")
    parser.add_argument("traccia",
                        help="""Nome del file che contiene i dati per effettuare il plot"""
                        )
    args = parser.parse_args()
    
    if not os.path.isfile(args.traccia):
        print("Il percorso specificato non è un file")
        sys.exit(1)
    
    if args.output:
        output = args.output
    else:
        output = args.traccia + "_plot.png"
    
    if args.titolo:
        titolo = args.titolo
    else:
        titolo = args.traccia
        
    mem_usata, timestamps = read_mem_usata(args.traccia)
    plot_memoria(mem_usata, timestamps, titolo, output, args.show)
    
def main():
    funzioni_comandi = {"run": run,
                        "track": track,
                        "plot": plot}
    funzioni_comandi[seleziona_comando()]()

if __name__ == "__main__":
    main()