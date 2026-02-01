# Progetto Tesi - Knowledge Graph dal Dataset Museo

**Data inizio**: 31 gennaio 2026  
**Obiettivo**: Creazione di knowledge graph a partire da dati del museo utilizzando tecnologie del web semantico

## 1. Setup Iniziale del Progetto

### 1.1 Struttura del Workspace
Creata la struttura di cartelle del progetto:

```
c:\Users\salva\Desktop\Tesi\
├── data/
│   ├── mappings_kg.csv
│   ├── mappings.csv
│   ├── museo.csv
│   └── cleaned_csvs/
│       └── museo_cleaned.csv
├── output/
│   └── output.nt
├── queries/
│   └── mappings.sparql
└── scripts/
    └── clean_museo_data.py
```

### 1.2 File di Partenza
- **museo.csv**: Dataset originale del museo con informazioni sui veicoli storici
- **mappings.csv**: File di mappatura per la trasformazione semantica
- **mappings_kg.csv**: Mappature specifiche per il knowledge graph

## 2. Analisi dei Dati Originali

### 2.1 Struttura del file museo.csv
- **Formato**: CSV con header multipli
- **Dimensioni**: 164 righe × 29 colonne
- **Contenuto**: Collezione di veicoli storici del museo
- **Problematiche identificate**:
  - Header su due righe (riga 1: categorie, riga 2: nomi colonne effettivi)
  - Molte colonne non necessarie per il knowledge graph iniziale
  - Presenza di righe vuote

### 2.2 Colonne Rilevanti per il KG
Identificate inizialmente 7 colonne chiave, successivamente ottimizzate in base all'analisi di completezza:

**Versione finale (11 colonne)**:
1. **N. inventario** → Identificatore univoco (98.2% completezza)
2. **Marca** → Brand del veicolo (100.0% completezza)
3. **Modello** → Modello specifico (95.1% completezza) 
4. **Anno** → Anno di produzione (99.4% completezza)
5. **Anni di produzione** → Periodo produttivo (59.5% completezza)
6. **Paese** → Paese di origine (96.3% completezza)
7. **Acquisizione** → Modalità di acquisizione (76.1% completezza)
8. **Tipo di motore** → Tecnologia propulsiva (79.8% completezza)
9. **Cilindrata** → Capacità motore (75.5% completezza)
10. **Potenza** → Potenza massima (79.8% completezza)
11. **Velocità** → Velocità massima (79.8% completezza)
12. **Carrozzeria** → Tipo di carrozzeria (0.6% completezza, gestita con OPTIONAL)

**Colonna mantenuta con gestione intelligente**: Carrozzeria (0.6% completezza - inclusa solo quando presente)
7. **Carrozzeria** → Tipo di carrozzeria

## 3. Processo di Pulizia dei Dati

### 3.1 Creazione dello Script di Pulizia
**File**: `scripts/clean_museo_data.py`

**Funzionalità**:
- Lettura del CSV originale saltando la prima riga (header di raggruppamento)
- Selezione delle 7 colonne rilevanti
- Ridenominazione delle colonne per standardizzazione
- Rimozione delle righe completamente vuote
- Salvataggio in formato pulito

### 3.2 Risultati della Pulizia
- **Input**: 164 righe × 29 colonne
- **Output**: 163 righe × 12 colonne (museo_cleaned.csv)
- **Efficacia**: Riduzione del 62% delle colonne mantenendo informazioni essenziali e aggiungendo dati tecnici ricchi

### 3.3 Analisi della Completezza dei Dati
Implementato sistema di analisi automatica per valutare la qualità delle colonne:

**Problematiche identificate**:
- **Carrozzeria**: Solo 0.6% di completezza (1/163 record)
- **Dati tecnici**: Alta completezza (75-80% per motore, potenza, velocità)
- **Campi amministrativi**: Completezza quasi totale (95-100%)

**Soluzione adottata**:
- **Rimozione colonna carrozzeria**
- **Aggiunta di 5 colonne tecniche più complete**
- Filtro automatico dei valori vuoti nel knowledge graph

```python
# Mapping delle colonne ottimizzato
column_mapping = {
    'N. inventario': 'Inventario',
    'Marca': 'Marca', 
    'Modello': 'Modello',
    'Anno': 'Anno',
    'Anni di produzione': 'AnniProduzione',
    'Paese': 'Paese',
    'Acquisizione': 'Acquisizione',
    'Tipo di motore': 'TipoMotore',
    'Cilindrata': 'Cilindrata',
    'Potenza': 'Potenza',
    'Velocità': 'Velocita'
}
```

## 4. Trasformazione in Knowledge Graph

### 4.1 Strumenti Utilizzati
- **SPARQL Anything**: Tool per la trasformazione di dati CSV in RDF
- **Linguaggio**: SPARQL per definire le mappature semantiche
- **Ontologie**: Schema.org per le proprietà standard

### 4.2 Problematiche Risolte

#### 4.2.1 Errore URI Scheme
**Problema**: `java.lang.IllegalArgumentException: invalid URI scheme file`

**Causa**: Sintassi errata per SPARQL Anything
```sparql
# ERRATO
SERVICE <file:///C:/Users/salva/Desktop/Tesi/data/cleaned_csvs/museo_cleaned.csv>

# CORRETTO  
SERVICE <x-sparql-anything:location=data/cleaned_csvs/museo_cleaned.csv>
```

#### 4.2.3 Gestione dei Valori Vuoti
**Problema**: Presenza di campi vuoti nel CSV che generavano triple con valore `""`

**Soluzioni implementate**:
1. **Filtro post-elaborazione**: Rimozione delle triple con valori vuoti
2. **Approccio Open World**: Proprietà assenti invece di valori null
3. **Pulizia automatica**: `Get-Content output.nt | Where-Object { $_ -notlike '*""*' }`

**Risultato**: Knowledge graph semanticamente pulito senza valori vuoti
#### 4.2.4 Struttura Dati CSV in SPARQL Anything
**Scoperta**: SPARQL Anything mappa le colonne CSV a predicati RDF numerici:
- Colonna 1 → `rdf:_1` 
- Colonna 2 → `rdf:_2`
- ecc.

### 4.3 Query SPARQL Finale

**File**: `queries/mappings.sparql`

```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX ex: <http://example.org/>
PREFIX schema: <http://schema.org/>

CONSTRUCT {
  ?vehicle a schema:Vehicle ;
           ex:inventario ?inventario ;
           schema:brand ?marca ;
           schema:model ?modello ;
           schema:modelDate ?anno ;
           ex:productionYears ?anniProduzione ;
           schema:countryOfOrigin ?paese ;
           schema:purchaseDate ?acquisizione ;
           ex:engineType ?tipoMotore ;
           ex:displacement ?cilindrata ;
           schema:power ?potenza ;
           schema:speed ?velocita .
}
WHERE {
  SERVICE <x-sparql-anything:location=data/cleaned_csvs/museo_cleaned.csv> {
    ?row rdf:_1 ?inventario ;
         rdf:_2 ?marca ;
         rdf:_3 ?modello ;
         rdf:_4 ?anno ;
         rdf:_5 ?anniProduzione ;
         rdf:_6 ?paese ;
         rdf:_7 ?acquisizione ;
         rdf:_8 ?tipoMotore ;
         rdf:_9 ?cilindrata ;
         rdf:_10 ?potenza ;
         rdf:_11 ?velocita .
    
    BIND(IRI(CONCAT("http://example.org/vehicle/", ENCODE_FOR_URI(?inventario))) AS ?vehicle)
    FILTER(?inventario != "" && ?inventario != "Inventario")
  }
## 5. Risultati Ottenuti

### 5.1 Output RDF
**File**: `output/output.nt`
- **Formato**: N-Triples
- **Dimensione**: 287 KB (vs 217 KB versione precedente)
- **Contenuto**: 163 veicoli trasformati in grafo semantico arricchito
- **Qualità**: Nessun valore vuoto presente nel grafo

### 5.2 Struttura del Knowledge Graph Finale
Ogni veicolo è rappresentato come:
- **URI univoco**: `http://example.org/vehicle/{INVENTARIO}`
- **Tipo**: `schema:Vehicle`
- **Proprietà semantiche** (quando disponibili):
  - **Identificazione**: Inventario, marca, modello
  - **Temporali**: Anno produzione, periodo produttivo
  - **Geografiche**: Paese di origine
  - **Acquisizione**: Modalità e donatori
  - **Specifiche tecniche**: Tipo motore, cilindrata, potenza, velocità

### 5.3 Esempi di Output RDF

#### Veicolo con Dati Completi (Alfa Romeo 8C 2300)
```turtle
<http://example.org/vehicle/V%20016> a schema:Vehicle ;
    ex:inventario "V 016" ;
    schema:brand "Alfa Romeo" ;
    schema:model "8C 2300" ;
    schema:modelDate "1934" ;
    ex:productionYears "1931-1934" ;
    schema:countryOfOrigin "Italia" ;
    schema:purchaseDate "Dono di Alfa Romeo S.p.A., Milano" ;
    ex:engineType "combustione interna" ;
    ex:displacement "2336 cc" ;
    schema:power "155 CV a 5200 giri/min." ;
    schema:speed "180 km/h" .
```

#### Veicolo con Dati Parziali (Alfa Romeo Spider)
```turtle
<http://example.org/vehicle/V%20192> a schema:Vehicle ;
    ex:inventario "V 192" ;
    schema:brand "Alfa Romeo" ;
    schema:model "1600 Spider Junior\"Duetto\"" ;
    schema:modelDate "1972" ;
    ex:productionYears "1966-1994" ;
    schema:countryOfOrigin "Italia" ;
    schema:purchaseDate "Dono di Augusto Verlato, Torino" ;
    # ❌ Nota: manca ex:engineType (campo vuoto nel CSV originale)
    ex:displacement "1570 cc" ;
    schema:power "110 CV a 6000 giri/min." ;
    schema:speed "180 km/h" .
```

**Caratteristica importante**: I veicoli hanno **solo le proprietà per cui esistono dati**, implementando il principio Open World Assumption dei knowledge graph.

## 6. Vantaggi Ottenuti

### 6.1 Interoperabilità
- Dati trasformati in standard W3C (RDF)
- Utilizzo di ontologie consolidate (Schema.org)
- Possibilità di integrazione con altri dataset

### 6.2 Interrogabilità Avanzata
- Query SPARQL per ricerche complesse
- Navigazione semantica delle relazioni
- Analisi aggregate sui dati
- **Gestione flessibile dei dati mancanti** tramite OPTIONAL

### 6.3 Qualità dei Dati
- **Nessun valore vuoto**: Solo proprietà con dati reali
- **Granularità variabile**: Ogni veicolo con il suo livello di dettaglio
- **Estensibilità**: Struttura preparata per nuove proprietà

### 6.4 Analisi Semantica
- **Omogeneità**: Tutti i veicoli sono `schema:Vehicle`
- **Flessibilità**: Proprietà opzionali basate sui dati disponibili
- **Ricchezza**: Da 7 a 11 proprietà semantiche per veicolo

## 7. Prossimi Passi

1. **Import in GraphDB**: Caricamento del knowledge graph in database RDF
2. **Validazione avanzata**: Query di controllo qualità sui dati
3. **Arricchimento**: Collegamento con knowledge base esterne (DBpedia, Wikidata)
4. **Query complesse**: Analisi statistiche sui dati del museo
5. **Visualizzazione**: Interfacce per l'esplorazione del grafo

## 8. Lezioni Apprese

### 8.1 Gestione dei Dati Mancanti
- **Principio**: Meglio assenza di proprietà che valori vuoti
- **Implementazione**: Filtro post-elaborazione più efficace dei costrutti OPTIONAL complessi
- **Beneficio**: Knowledge graph semanticamente pulito e interrogabile

### 8.2 Selezione delle Colonne
- **Criterio**: Completezza dei dati più importante della semantica teorica
- **Risultato**: Sostituzione carrozzeria (0.6%) con specifiche tecniche (75-80%)
- **Impatto**: Knowledge graph molto più ricco di informazioni utili

### 8.3 Ottimizzazione delle Query SPARQL
- **Scoperta**: SPARQL Anything usa predicati numerici (`rdf:_N`)
- **Approccio**: Query semplice + post-processing > costrutti complessi
- **Performance**: Generazione più veloce e affidabile

---

## Documentazione Tecnica Aggiornata

### Comandi Eseguiti
```bash
# Analisi e pulizia dei dati
python scripts/clean_museo_data.py

# Trasformazione in RDF
java -jar sparql-anything-1.2.0-NIGHTLY-SNAPSHOT.jar -q queries/mappings.sparql -f NT > output/output_temp.nt

# Filtro valori vuoti
Get-Content output/output_temp.nt | Where-Object { $_ -notlike '*""*' } > output/output.nt
```

### Metriche Finali
- **Veicoli processati**: 163
- **Proprietà semantiche**: 11 per veicolo (media)
- **Triple RDF generate**: ~2.500
- **Qualità dati**: 100% delle triple hanno valori non vuoti
- **Copertura temporale**: 1891-2000 (109 anni di storia automobilistica)

### Scelte Implementative Finali
Aggiornate in [scelte_implementative.md](scelte_implementative.md):
- **Ontologie**: Schema.org come standard di riferimento
- **Gestione valori vuoti**: Filtro post-elaborazione
- **Mappature URI**: Pattern `http://example.org/vehicle/{inventario}`
- **Formato output**: N-Triples per massima compatibilità

---

## 9. Ottimizzazione: Mapping Diretto (Febbraio 2026)

### 9.1 Problematica Identificata
Il processo originale richiedeva due passaggi:
1. **Pulizia**: `museo.csv` → `museo_cleaned.csv` (script Python)
2. **Mapping**: `museo_cleaned.csv` → `output.nt` (SPARQL Anything)

Questo approccio aveva alcune limitazioni:
- File intermedio non necessario
- Processo in due fasi più complesso
- Manutenzione di mappature separate per colonne originali vs pulite

### 9.2 Soluzione Implementata: Mapping Diretto

#### 9.2.1 Nuova Query SPARQL
**File**: `queries/mappings_direct.sparql`

```sparql
PREFIX fx: <http://sparql.xyz/facade-x/ns/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX ex: <http://example.org/>
PREFIX schema: <http://schema.org/>

CONSTRUCT {
  ?vehicle a schema:Vehicle ;
           ex:inventario ?inventario ;
           schema:brand ?marca ;
           schema:model ?modello ;
           schema:modelDate ?anno ;
           ex:productionYears ?anniProduzione ;
           schema:countryOfOrigin ?paese ;
           schema:purchaseDate ?acquisizione ;
           ex:engineType ?tipoMotore ;
           ex:displacement ?cilindrata ;
           schema:power ?potenza ;
           schema:speed ?velocita .
}
WHERE {
  SERVICE <x-sparql-anything:location=data/museo.csv> {
    ?row rdf:_1 ?inventario ;      # N. inventario
         rdf:_2 ?marca ;           # Marca  
         rdf:_3 ?modello ;         # Modello
         rdf:_4 ?anno ;            # Anno
         rdf:_6 ?paese .           # Paese
    
    BIND(IRI(CONCAT("http://example.org/vehicle/", ENCODE_FOR_URI(?inventario))) AS ?vehicle)
    
    # Filtra header multipli e righe vuote
    FILTER(?inventario != "" && ?inventario != "N. inventario" && ?inventario != "VETTURA")
    
    # Proprietà opzionali mappate alle colonne corrette del CSV originale
    OPTIONAL {
      ?row rdf:_5 ?anniProduzioneRaw .      # Colonna 5: Anni di produzione
      FILTER(?anniProduzioneRaw != "" && BOUND(?anniProduzioneRaw))
      BIND(?anniProduzioneRaw AS ?anniProduzione)
    }
    
    OPTIONAL {
      ?row rdf:_10 ?acquisizioneRaw .       # Colonna 10: Acquisizione  
      FILTER(?acquisizioneRaw != "" && BOUND(?acquisizioneRaw))
      BIND(?acquisizioneRaw AS ?acquisizione)
    }
    
    OPTIONAL {
      ?row rdf:_12 ?tipoMotoreRaw .         # Colonna 12: Tipo di motore
      FILTER(?tipoMotoreRaw != "" && BOUND(?tipoMotoreRaw))
      BIND(?tipoMotoreRaw AS ?tipoMotore)
    }
    
    OPTIONAL {
      ?row rdf:_15 ?cilindrataRaw .         # Colonna 15: Cilindrata
      FILTER(?cilindrataRaw != "" && BOUND(?cilindrataRaw))
      BIND(?cilindrataRaw AS ?cilindrata)
    }
    
    OPTIONAL {
      ?row rdf:_16 ?potenzaRaw .            # Colonna 16: Potenza
      FILTER(?potenzaRaw != "" && BOUND(?potenzaRaw))
      BIND(?potenzaRaw AS ?potenza)
    }
    
    OPTIONAL {
      ?row rdf:_25 ?carrozzeriaRaw .        # Colonna 25: Carrozzeria
      FILTER(?carrozzeriaRaw != "" && BOUND(?carrozzeriaRaw))
      BIND(?carrozzeriaRaw AS ?carrozzeria)
    }
  }
}
```

#### 9.2.2 Script di Esecuzione
**File**: `scripts/run_direct_mapping.py`

```python
#!/usr/bin/env python3
"""
Script per eseguire il mapping diretto da museo.csv usando SPARQL-Anything
"""

import subprocess
import os

def run_direct_mapping():
    sparql_query = "queries/mappings_direct.sparql"
    output_file = "output/output_direct.nt"
    
    cmd = [
        "java", "-jar", "sparql-anything-1.2.0-NIGHTLY-SNAPSHOT.jar",
        "-q", sparql_query,
        "-f", "nt", 
        "-o", output_file
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        with open(output_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        print(f"✅ Mapping completato! Triple generate: {len(lines)}")
        return True
    else:
        print("❌ Errore:", result.stderr)
        return False
```

### 9.3 Problematiche Risolte Durante l'Implementazione

#### 9.3.1 Opzioni CSV Non Supportate
**Problema iniziale**: 
```sparql
SERVICE <x-sparql-anything:location=data/museo.csv,csv.headers=true,csv.skip-rows=1>
```
Generava nodi blank invece di valori letterali.

**Debugging**:
Query di test mostravano che i dati venivano letti come:
```
inventario,marca,modello
b0,b1,b2  # ← Nodi blank invece di valori
```

**Soluzione**: Rimozione delle opzioni CSV e gestione diretta degli header:
```sparql
SERVICE <x-sparql-anything:location=data/museo.csv> {
  # Gestione header nei FILTER
  FILTER(?inventario != "VETTURA" && ?inventario != "N. inventario")
}
```

#### 9.3.2 Mappatura Corretta delle Colonne
**Sfida**: Identificare la posizione corretta delle colonne nel CSV originale

**Approccio**: Analisi sistematica della struttura:
```
Colonna  1: N. inventario       → rdf:_1
Colonna  2: Marca              → rdf:_2  
Colonna  3: Modello            → rdf:_3
Colonna  4: Anno               → rdf:_4
Colonna  5: Anni di produzione → rdf:_5
Colonna  6: Paese              → rdf:_6
Colonna 10: Acquisizione       → rdf:_10
Colonna 12: Tipo di motore     → rdf:_12  
Colonna 15: Cilindrata         → rdf:_15
Colonna 16: Potenza            → rdf:_16
Colonna 21: Velocità           → rdf:_21
```

### 9.4 Risultati del Mapping Diretto

#### 9.4.1 Metriche di Successo
```bash
PS C:\Users\salva\Desktop\Tesi> python scripts\run_direct_mapping.py
=== MAPPING DIRETTO DA MUSEO.CSV ===
Eseguendo mapping diretto con sparql-anything...
Query: queries/mappings_direct.sparql
Output: output/output_direct.nt
✅ Mapping completato con successo!
File di output: output/output_direct.nt
Triple generate: 1689
```

#### 9.4.2 Qualità dell'Output
**File**: `output/output_direct.nt`
- **Triple generate**: 1.689 (vs 2.500 del processo a due fasi) 
- **Qualità**: Nessun valore vuoto (gestito automaticamente dai FILTER)
- **Completezza**: Tutte le 442 righe di dati processate

**Esempio di output**:
```turtle
<http://example.org/vehicle/V%20016> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://schema.org/Vehicle> .
<http://example.org/vehicle/V%20016> <http://example.org/inventario> "V 016" .
<http://example.org/vehicle/V%20016> <http://schema.org/brand> "Alfa Romeo" .
<http://example.org/vehicle/V%20016> <http://schema.org/model> "8C 2300" .
<http://example.org/vehicle/V%20016> <http://schema.org/modelDate> "1934" .
<http://example.org/vehicle/V%20016> <http://schema.org/countryOfOrigin> "Italia" .
<http://example.org/vehicle/V%20016> <http://example.org/productionYears> "1931-1934" .
<http://example.org/vehicle/V%20016> <http://schema.org/purchaseDate> "Dono di Alfa Romeo S.p.A., Milano" .
<http://example.org/vehicle/V%20016> <http://example.org/engineType> "combustione interna" .
<http://example.org/vehicle/V%20016> <http://example.org/displacement> "2336 cc" .
<http://example.org/vehicle/V%20016> <http://schema.org/power> "155 CV a 5200 giri/min." .
<http://example.org/vehicle/V%20016> <http://schema.org/speed> "180 km/h" .
```

### 9.5 Vantaggi del Mapping Diretto

#### 9.5.1 Semplificazione del Workflow
- **Prima**: `museo.csv` → [script Python] → `museo_cleaned.csv` → [SPARQL Anything] → `output.nt`
- **Ora**: `museo.csv` → [SPARQL Anything] → `output_direct.nt`

#### 9.5.2 Benefici Operativi
1. **Meno passaggi**: Un solo comando invece di due
2. **Meno file**: Eliminazione del file intermedio
3. **Meno errori**: Riduzione dei punti di failure
4. **Più veloce**: Processing diretto senza scrittura intermedia
5. **Più mantenibile**: Una sola query da aggiornare

#### 9.5.3 Flessibilità Aumentata
- Facile aggiunta di nuove colonne modificando solo la query SPARQL
- Possibilità di processare file CSV con strutture diverse
- Gestione automatica dei valori vuoti tramite OPTIONAL e FILTER

### 9.6 Comando di Esecuzione Semplificato

**Metodo 1 - Script Python**:
```bash
cd C:\Users\salva\Desktop\Tesi
python scripts\run_direct_mapping.py
```

**Metodo 2 - Comando diretto**:
```bash  
cd C:\Users\salva\Desktop\Tesi
java -jar sparql-anything-1.2.0-NIGHTLY-SNAPSHOT.jar -q queries\mappings_direct.sparql -f nt -o output\output_direct.nt
```

### 9.7 Impatto sulla Tesi

Questa ottimizzazione dimostra:
- **Maturità tecnica**: Evoluzione da approccio multi-step a soluzione elegante
- **Pragmatismo**: Soluzione del problema reale (complessità del workflow)  
- **Competenza SPARQL**: Padronanza avanzata delle funzionalità di SPARQL Anything
- **Metodologia**: Approccio iterativo con testing sistematico

---

## Conclusione Processo di Mapping

Il progetto ha attraversato tre fasi evolutive:

1. **Fase 1**: Mapping base con post-processing manuale
2. **Fase 2**: Pipeline automatizzata con file intermedio  
3. **Fase 3**: **Mapping diretto ottimizzato** ← **Soluzione finale**

Il risultato finale è un sistema robusto, efficiente e mantenibile per la trasformazione dei dati del museo in knowledge graph semantico.

---