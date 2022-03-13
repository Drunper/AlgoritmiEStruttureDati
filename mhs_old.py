# -*- coding: utf-8 -*-
"""
Created on Mon Jan 7 11:07:53 2022

@author: patri
"""

import re, linecache, sys, os
import queue, array as arr
import numpy as np
from collections import deque
from time import process_time
from argparse import ArgumentParser, RawTextHelpFormatter
from memory_profiler import memory_usage
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
terminazione_anticipata = False
def read_mat(file): 
  data = []
  for line in file:
    if line[0] != ";":
      newLine = line.replace("-","")
      l = newLine.split(" ")
      l.remove("\n")     
      data.append(arr.array('B', list(map(int, l))))
  file.close()
  return data

def read_mat_np(file): 
  data = []
  for line in file:
    if line[0] != ";":
      newLine = line.replace("-","")
      l = newLine.split(" ")
      l.remove("\n")
      data.append(l)
  file.close()
  d = np.array(data, dtype = np.uint8) 
  return d

def array_dominio(nome_file):
  line = linecache.getline(nome_file, 5)
  dom=re.findall('\(([^)]+)', line)
  array = list(dom)
  return array  

def leggi_dizionario_dominio(nome_file):
  line = linecache.getline(nome_file, 5)
  dom=re.findall('\(([^)]+)', line)
  dicts = {}
  keys = range(len(dom))
  for i in keys:
    dicts[i] = dom[i]
  return dicts

def leggi_matrice(percorso_file, versione):
  f= open(percorso_file,"r")
  if versione == 0:
      array_matrice = read_mat(f)
  elif versione == 1 or versione == 2:
      array_matrice = read_mat_np(f)
  print("------- array originale dim: ----")
  print(len(array_matrice), len(array_matrice[0]))
  dominioBase = array_dominio(percorso_file)
  print("Verifica dimensioni:")
  if len(array_matrice[0]) == len(dominioBase):
    print("OK DIMENSIONI COINCIDONO !!")
  else: 
    print("ERRORE SU DIMENSIONI FILE !!")
    sys.exit()
  print("-------array dom originale: ----")
  print("Len dom: " + str(len(dominioBase)))

  if versione == 0 or versione == 2:
      dominioBase = list(range(0, len(array_matrice[0])))
  return array_matrice, dominioBase, len(array_matrice), len(array_matrice[0])

def replace_value(A, dominio):
  M=A.shape[1]
  N=A.shape[0]
  newArray= np.array(A, dtype='U4')
  for r in range(N):
    for c in range(M):
      if newArray[r,c]=="1":
        newArray[r,c]=dominio[c]   
  return newArray

def succ_mem(M,elem):  
  if elem==-1: 
    val= M[0]
  elif elem == M[-1]:
    val= -11 
  else:
    indice=M.index(elem)
    val= M[indice+1]
  return val

def max_vett_mem(v):
  if not v: 
    return -1
  else: 
    return v[-1]

def succ(M,elem):  
  if elem==-1: val= 1
  elif elem == M: val= -11 #eps-max
  else:
    val=elem+1
  return val

def max_vett(v):
  if not v: return -1
  else: return v[-1]

def alg_base_packbits(A, dominio, colonne):
  global terminazione_anticipata
  start_time=process_time()
  lista_mhs=[]  
  queue=deque() 
  queue.append(([],[]))
  try:
    while queue:
      insieme = queue.popleft()
      e = succ(colonne,max_vett(insieme[0]))
        
      if e!= -11: 
        ind, offset = divmod(e-1, 8)
        d = np.unpackbits(A[None, :, ind], axis=0, count=8)
        for elem in range(e,colonne+1):
          if offset == 8:
            ind = ind + 1
            offset = 0
            d = np.unpackbits(A[None, :, ind], axis=0, count=8)
          vett_rapp= crea_vett_rapp_packbits(insieme,d[offset],elem)      
          result= check_packbits(vett_rapp)
          if result=="ok" and elem != colonne:
            queue.append(vett_rapp)    
          elif result=="mhs":
            output(vett_rapp[0], dominio)
            lista_mhs.append(vett_rapp[0])
          offset = offset + 1
  except KeyboardInterrupt:
    print("Esecuzione terminata dall'utente\n")
    terminazione_anticipata = True
  return lista_mhs, process_time() - start_time

def check_packbits(vettore):
  proiezione= set(vettore[1]) 
  esistono=True
  i = 0
  while i < len(vettore[0]) and esistono:
    if vettore[0][i] not in proiezione:
      esistono=False
    i = i + 1
 
  if esistono==True:
    if 0 in proiezione:
      return "ok"
    else:
      return "mhs"
  else: 
    return "ko"  
    

def crea_vett_rapp_packbits(start,added,e_succ): 
  if not start[0]:
   base = []
   base.append(e_succ)
   vr = (base, list(added*e_succ))   
  else:
    vr = (list(start[0]), list(start[1]))
    vr[0].append(e_succ)
    for i in range(len(vr[1])):
      if vr[1][i] != "x":
        if added[i]:
          if not vr[1][i]:
            vr[1][i] = e_succ
          else:
            vr[1][i] = "x"
  return vr


def output(mhs, dominio):
  for i in range(len(mhs)):
    mhs[i] = dominio[mhs[i]-1]

def alg_base_memoria(A,M):
  global terminazione_anticipata
  start_time=process_time()
  output=[]  
  trasposta=np.transpose(A)
  ultimo= M[-1]
  queue=deque() 
  queue.append( [ [] , [] ] )
  try:
    while queue:
      insieme= queue.popleft()
      e= succ_mem(M,max_vett_mem(insieme[0]))
      if e!= -11: 
        index_of_e= M.index(e)      
        for index_of_e in range(index_of_e,len(M)):   
          e= M[index_of_e]
          vett_rapp= crea_vett_rapp_mem(insieme,trasposta[index_of_e],e)      
          result= check_mem(vett_rapp)
          if result=="ok" and e!= ultimo:
            queue.append(vett_rapp)    
          elif result=="mhs":
            output.append(vett_rapp[0])
            del vett_rapp[1]
            
  except KeyboardInterrupt:
    print("Esecuzione terminata dall'utente\n")
    terminazione_anticipata = True
         
  return output, process_time() - start_time

def check_mem(vettore):
  proiezione= set(vettore[1]) 
  zeroExist=False
  esistono=True
  for i in range(len(vettore[0])):
    if vettore[0][i] not in proiezione:
      esistono=False
      break
 
  for item in proiezione:
    if item=="0":
      zeroExist=True
      break

  if esistono==True and zeroExist:
    return "ok"
  elif esistono==True and not zeroExist:
    return "mhs"
  else: return "ko"   
    

def crea_vett_rapp_mem(start,sing,e_succ): 
  vr=[[],[]]
  if not start[0]:
   vr[0].append(e_succ)
   vr[1]=list(sing)    
       
  else :
    vr[0]=list(start[0])
    vr[0].append(e_succ)
    vr[1]= [None]*(len(sing))
    length=len(start[1])
    for i in range(length):
      if start[1][i]== "0" and sing[i]== "0":
        vr[1][i]= "0"
      elif (start[1][i]!="0" and start[1][i]!="x") and sing[i]=="0":
        vr[1][i]= start[1][i]  
      elif start[1][i] =="0" and (sing[i] !="0" and sing[i] !="x"):
        vr[1][i]= sing[i]
      else: vr[1][i]= "x"
  return vr

def succ_no_mem(elem): 
  if elem == -1: 
    return 1
  else:
    return elem + 1

def max_insieme_no_mem(insieme):
  if not insieme: 
    return -1
  else: 
    return insieme[-1]

def alg_base_no_memoria(A, dominio):
  global terminazione_anticipata
  start_time=process_time()
  lista_mhs=[]  
  queue=deque()
  valore_max = len(A[0]) 
  queue.append(arr.array('I', []))
  vett_rapp = arr.array('I', [0] * len(A))
  try:
    while queue:
      insieme = queue.popleft()
      e = succ_no_mem(max_insieme_no_mem(insieme))
    
      for elem in range(e,valore_max+1):
        nuovo_insieme = insieme.tolist() 
        nuovo_insieme.append(elem)
        nuovo_insieme = arr.array('I', nuovo_insieme) 
        crea_vett_rapp_no_mem(nuovo_insieme, vett_rapp, A)     
        result = check_no_mem(nuovo_insieme, vett_rapp)
        if result == "ok" and elem != valore_max:
          queue.append(nuovo_insieme)    
        elif result == "mhs":
          output(nuovo_insieme, dominio)
          lista_mhs.append(nuovo_insieme)
  except KeyboardInterrupt:
    print("Esecuzione terminata dall'utente\n")
    terminazione_anticipata = True
    
  return lista_mhs, process_time() - start_time

def check_no_mem(nuovo_insieme, vettore):
  proiezione= set(vettore) 
  for i in nuovo_insieme:
    if i not in proiezione:
      return "ko" 
 
  if 0 in proiezione:
    return "ok"
  else:
    return "mhs"  

def crea_vett_rapp_no_mem(insieme, vett_rapp, A): 
  for i in range(len(A)):
    vett_rapp[i] = 0
    for j in insieme:
      if A[i][j-1]:
        if vett_rapp[i]:
          vett_rapp[i] = 65535 
          break
        else:
          vett_rapp[i] = j

def contiene(A, first, second): 
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

def togli_righe_no_np(A): 
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
  return l, len(l) 

def colonna_di_zeri(A, i):
  for j in range(len(A)):
    if A[j][i]:
      return False
  return True

def resize_dom_array(dom,indiciDaTogliere):
  new_dom = dom.copy()
  if indiciDaTogliere:
    for i in range(len(indiciDaTogliere)-1,-1,-1):  
      del new_dom[indiciDaTogliere[i]]
  return new_dom 

def togli_colonne_no_np(A):
  l = []
  for i in range(len(A[0])):
    if colonna_di_zeri(A, i):
      l.append(i)
  for i in reversed(l):
    deque(map(lambda x: x.pop(i), A), maxlen=0)
  return l, len(l) 

def togli_righe_np(A):
  l = costruisci_lista(A)
  indici = [] 
  for i in range(len(l)):
    k = i + 1
    stop = False
    while k < A.shape[0] and not stop:
      if contiene(A, l[i], l[k]):
        indici.append(l[i]) # 
        stop = True 
      k = k + 1
  return np.delete(A, indici, 0), indici, len(indici) 

def togli_colonne_np(A):
  l = []
  for i in range(A.shape[1]):
    if colonna_di_zeri(A, i):
      l.append(i)
  return np.delete(A, l, 1), l, len(l) 

def alg_base(A, dominio, colonne_originali, versione):
  if versione == 0:
    return alg_base_no_memoria(A, dominio)
  elif versione == 1:
    A = replace_value(A, dominio)
    return alg_base_memoria(A, dominio)
  elif versione == 2:
    B = np.packbits(A, axis=-1)
    return alg_base_packbits(B, dominio, A.shape[1])

def alg_con_pre(A, dominio, colonne_originali, versione):
  print("Inizio pre-elaborazione")
  if versione == 1 or versione == 2:
      A, indici_righe_rimosse, numero_righe_rimosse = togli_righe_np(A)
      A, indici_colonne_rimosse, numero_colonne_rimosse = togli_colonne_np(A)
  elif versione == 0:
      indici_righe_rimosse, numero_righe_rimosse = togli_righe_no_np(A)
      indici_colonne_rimosse, numero_colonne_rimosse = togli_colonne_no_np(A)
  dominio_pre_elaborato = resize_dom_array(dominio, indici_colonne_rimosse)
  print("Pre-elaborazione terminata")
  lista_mhs, tempo_di_esecuzione_base = alg_base(A, dominio_pre_elaborato, colonne_originali, versione)
  return lista_mhs, tempo_di_esecuzione_base, numero_righe_rimosse, numero_colonne_rimosse, indici_righe_rimosse, indici_colonne_rimosse, dominio_pre_elaborato

def max_min_mhs(lista_mhs):
  return len(max(lista_mhs, key = len)), len(min(lista_mhs, key = len))
               
def stringa_da_array(array):
  if array:
    separatore = " "
    stringa = separatore.join([str(elem) for elem in array])
    return f'{stringa} -\n'
  else:
    return '\n'
    
def converti_mhs_dominio(lista, colonne, dominio):
  l = [0] * colonne
  for elem in lista:
    l[elem] = 1
  return arr.array('B', l)

def converti_mhs_dizionario(lista, colonne, dizionario):
  l = [0] * colonne
  for elem in lista:
    l[dizionario[elem]] = 1
  return arr.array('B', l)
    
    
def scrivi_risultati(nome_file, versione, nome_matrice, dimensione_matrice, mhs_trovati, dimensioni_mhs, 
                     tempo_di_esecuzione_base, lista_mhs, dominio, dizionario_dominio, pre_elaborazione, righe_rimosse=None, colonne_rimosse=None, 
                     indici_righe=None, indici_colonne=None):
  global terminazione_anticipata
  with open(nome_file, 'w') as output_file:
    if pre_elaborazione:
      output_file.write('Report esecuzione algoritmo con pre-elaborazione\n')
    else:
      output_file.write('Report esecuzione algoritmo base\n')
    if versione == 0:
      output_file.write('Versione: no memorizzazione vettori rappresentativi\n')
    elif versione == 1:
      output_file.write('Versione: memorizzazione vettori rappresentativi\n')
    elif versione == 2:
      output_file.write('Versione: memorizzazione vettori rappresentativi + uso packbits\n')
      
    output_file.write(f'Nome matrice: {nome_matrice}\n')
    output_file.write(f'Numero righe: {dimensione_matrice[0]}\n')
    output_file.write(f'Numero colonne: {dimensione_matrice[1]}\n')
    output_file.write('\n')
        
    if pre_elaborazione:
      output_file.write('Pre-elaborazione\n')
      output_file.write(f'Righe rimosse: {righe_rimosse}\n')
      output_file.write(f'Colonne rimosse: {colonne_rimosse}\n')
      output_file.write('Indici righe rimosse:\n')
      output_file.write(stringa_da_array(indici_righe))
      output_file.write('Indici colonne rimosse:\n')
      output_file.write(stringa_da_array(indici_colonne))
      output_file.write('\n')
        
    if terminazione_anticipata:
      output_file.write("Esecuzione: interrotta dall'utente\n")
    else:
      output_file.write('Esecuzione: completata\n')
        
    output_file.write(f'Numero MHS trovati: {mhs_trovati}\n')
    output_file.write(f'Cardinalità minima MHS: {dimensioni_mhs[1]}\n')
    output_file.write(f'Cardinalità massima MHS: {dimensioni_mhs[0]}\n')
        
    output_file.write('\n')
    output_file.write(f'Tempo di esecuzione algoritmo: {tempo_di_esecuzione_base}\n')
                
  mhs_file = ""
  if pre_elaborazione:
    mhs_file = f'MHS_p_{nome_matrice}.txt'
  else:
    mhs_file = f'MHS_{nome_matrice}.txt'
  with open(mhs_file, 'w') as output_file:
    output_file.write('MHS trovati:\n')
    if versione == 1:
      for mhs in lista_mhs:
        output_file.write(stringa_da_array(converti_mhs_dizionario(mhs, dimensione_matrice[1], dizionario_dominio)))
    else:
      for mhs in lista_mhs:
        output_file.write(stringa_da_array(converti_mhs_dominio(mhs, dimensione_matrice[1], dominio)))

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
    sys.exit()
  if not sys.argv[1] in comandi_disponibili:
    print(messaggio_help)
    sys.exit()
  return sys.argv.pop(1)

def run():
  parser = ArgumentParser(usage="mhs run [opzioni] matrix", formatter_class=RawTextHelpFormatter)
  parser.add_argument("-p", "--preelaborazione", dest="pre_elaborazione", action="store_true",
                      help="""Effettua la pre-elaborazione (rimozione righe e colonne) della matrice prima di applicare l'algoritmo""")
  parser.add_argument("-o", "--output", dest="output",                       
                      help="""Nome del file in cui verrà salvato il report riguardante l'esecuzione dell'algoritmo sulla matrice di input""")
  parser.add_argument("-v", "--versione", dest="versione", type=int, choices=range(0,3), default=0,
                      help="""Versione dell'algoritmo da eseguire""")
  parser.add_argument("matrix",
                      help="""Nome del file che contiene la matrice di input""")
  args = parser.parse_args()
    
  if not os.path.isfile(args.matrix):
    print("Il percorso specificato non è un file")
    sys.exit()
        
  if args.versione < 0 or args.versione > 2 or not isinstance(args.versione, int):
    print("Numero di versione non valido")
    sys.exit()
        
  nome_matrice = os.path.splitext(args.matrix)[0]
    
  if args.output:
    output = args.output
  elif args.pre_elaborazione:
    output = f'Risultati_p_{nome_matrice}.txt'
  else:
    output = f'Risultati_{nome_matrice}.txt'
    
  array_matrice, dominio_base, righe, colonne = leggi_matrice(args.matrix, args.versione)
  dimensione_matrice = (righe, colonne)
    
  if args.versione == 1:
    dizionario_dominio = leggi_dizionario_dominio(args.matrix)
  else:
    dizionario_dominio = None
    
  print("Premi CTRL+C per interrompere l'esecuzione del programma")
  if args.pre_elaborazione:
    lista_mhs, tempo_di_esecuzione_base, righe_rimosse, colonne_rimosse, indici_righe, indici_colonne, dominio_pre_elaborato = alg_con_pre(array_matrice, dominio_base, colonne, args.versione)
    if args.versione == 1:
      dizionario_dominio = resize_dom_array(dizionario_dominio, indici_colonne)
    mhs_trovati = len(lista_mhs)
    dimensioni_mhs = max_min_mhs(lista_mhs)
  else:
    lista_mhs, tempo_di_esecuzione_base = alg_base(array_matrice, dominio_base, colonne, args.versione)
    mhs_trovati = len(lista_mhs)
    dimensioni_mhs = max_min_mhs(lista_mhs)
  print("Esecuzione terminata, scrittura risultati su file in corso...")
    
  if args.versione == 1:
    dizionario_dominio = {v: k for k, v in dizionario_dominio.items()}
    
  if args.pre_elaborazione:
    scrivi_risultati(output, args.versione, nome_matrice, dimensione_matrice, mhs_trovati, dimensioni_mhs, 
                     tempo_di_esecuzione_base, lista_mhs, dominio_pre_elaborato, dizionario_dominio, True, 
                     righe_rimosse, colonne_rimosse, indici_righe, indici_colonne)
  else:
    scrivi_risultati(output, args.versione, nome_matrice, dimensione_matrice, mhs_trovati, dimensioni_mhs, 
                     tempo_di_esecuzione_base, lista_mhs, dominio_base, dizionario_dominio, False)
    
def track():
  parser = ArgumentParser(usage="mhs track [opzioni] matrix", formatter_class=RawTextHelpFormatter)
  parser.add_argument("-p", "--preelaborazione", dest="pre_elaborazione", action="store_true",
                      help="""Effettua la pre-elaborazione (rimozione righe e colonne) della matrice prima di applicare l'algoritmo""")
  parser.add_argument("-o", "--output", dest="output",                       
                      help="""Nome del file in cui verrà salvato il consumo di memoria nel tempo""")
  parser.add_argument("-v", "--versione", dest="versione", type=int, choices=range(0,3), default=0,
                      help="""Versione dell'algoritmo da eseguire""")
  parser.add_argument("matrix",
                      help="""Nome del file che contiene la matrice di input"""
                        )
  args = parser.parse_args()
    
  if not os.path.isfile(args.matrix):
    print("Il percorso specificato non è un file")
    sys.exit()
        
  if args.versione < 0 or args.versione > 2 or not isinstance(args.versione, int):
    print("Numero di versione non valido")
    sys.exit()
        
  nome_matrice = os.path.splitext(args.matrix)[0]
    
  if args.output:
    output = args.output
  elif args.pre_elaborazione:
    output = f'Track_mem_p_{nome_matrice}.txt'
  else:
    output = f'Track_mem_{nome_matrice}.txt'
    
  array_matrice, dominio_base, righe, colonne = leggi_matrice(args.matrix, args.versione)

  if args.pre_elaborazione:
    mem_usage = memory_usage(proc=(alg_con_pre, (array_matrice, dominio_base, colonne, args.versione),), timestamps=True)
  else:
    mem_usage = memory_usage(proc=(alg_base, (array_matrice, dominio_base, colonne, args.versione),), timestamps=True)  
  with open(output, "w") as f:
    f.write(f"Nome matrice: {nome_matrice}\n")
    for mem, timestamp in mem_usage:
      f.write(f"{mem:.6f} {timestamp:.4f}\n")
    
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
    sys.exit()
    
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
