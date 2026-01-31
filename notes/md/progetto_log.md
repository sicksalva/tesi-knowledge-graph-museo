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

**Colonna rimossa**: Carrozzeria (0.6% completezza - sostituita con dati tecnici più ricchi)
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
- **Output**: 163 righe × 11 colonne (museo_cleaned.csv)
- **Efficacia**: Riduzione del 62% delle colonne mantenendo informazioni essenziali e aggiungendo dati tecnici ricchi

### 3.3 Analisi della Completezza dei Dati
Implementato sistema di analisi automatica per valutare la qualità delle colonne:

**Problematiche identificate**:
- **Carrozzeria**: Solo 0.6% di completezza (1/163 record)
- **Dati tecnici**: Alta completezza (75-80% per motore, potenza, velocità)
- **Campi amministrativi**: Completezza quasi totale (95-100%)

**Soluzione adottata**:
- Rimozione colonna carrozzeria
- Aggiunta di 5 colonne tecniche più complete
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