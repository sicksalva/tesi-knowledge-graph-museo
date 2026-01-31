# Knowledge Graph per Museo Automobilistico

Progetto di tesi per la creazione di knowledge graph a partire da dati del museo utilizzando tecnologie del web semantico.

## 🎯 Obiettivi

- Trasformazione di dati CSV in knowledge graph RDF
- Utilizzo di SPARQL Anything per l'elaborazione
- Implementazione di best practices per la gestione dei dati mancanti
- Creazione di un grafo semantico pulito e interrogabile

## 📁 Struttura del Progetto

```
├── data/                          # Dataset originali e puliti
│   ├── museo.csv                 # Dataset originale (163 veicoli, 29 colonne)
│   ├── mappings.csv              # Mappature per trasformazioni
│   ├── mappings_kg.csv           # Mappature specifiche per KG
│   └── cleaned_csvs/
│       └── museo_cleaned.csv     # Dataset pulito (163 veicoli, 11 colonne)
├── scripts/                      # Script di elaborazione
│   └── clean_museo_data.py       # Pulizia e analisi completezza dati
├── queries/                      # Query SPARQL
│   ├── mappings.sparql          # Query principale per trasformazione RDF
│   └── debug.sparql             # Query di debug
├── output/                       # Risultati elaborazione
│   └── output.nt                # Knowledge graph in formato N-Triples (287KB)
└── notes/
    └── md/
        └── progetto_log.md       # Documentazione completa del progetto
```

## 🚀 Quick Start

### 1. Pulizia dei Dati
```bash
cd scripts
python clean_museo_data.py
```

### 2. Trasformazione in RDF
```bash
java -jar sparql-anything-1.2.0-NIGHTLY-SNAPSHOT.jar -q queries/mappings.sparql -f NT > output/output_temp.nt
```

### 3. Filtro Valori Vuoti
```powershell
Get-Content output/output_temp.nt | Where-Object { $_ -notlike '*""*' } > output/output.nt
```

## 📊 Risultati

- **163 veicoli** trasformati in knowledge graph
- **11 proprietà semantiche** per veicolo (quando disponibili)
- **~2.500 triple RDF** generate
- **100% qualità**: nessun valore vuoto nel grafo
- **Copertura temporale**: 1891-2000 (109 anni di storia automobilistica)

## 🔧 Tecnologie Utilizzate

- **SPARQL Anything**: Trasformazione CSV → RDF
- **Schema.org**: Ontologie standard
- **Python**: Analisi e pulizia dati
- **N-Triples**: Formato output RDF

## 📈 Esempi di Dati

### Veicolo Completo (Alfa Romeo 8C 2300)
```turtle
<http://example.org/vehicle/V%20016> a schema:Vehicle ;
    ex:inventario "V 016" ;
    schema:brand "Alfa Romeo" ;
    schema:model "8C 2300" ;
    schema:modelDate "1934" ;
    ex:productionYears "1931-1934" ;
    schema:countryOfOrigin "Italia" ;
    ex:engineType "combustione interna" ;
    ex:displacement "2336 cc" ;
    schema:power "155 CV a 5200 giri/min." ;
    schema:speed "180 km/h" .
```

## 🎓 Contributi Accademici

- **Gestione dati mancanti**: Implementazione principio Open World Assumption
- **Ottimizzazione colonne**: Analisi completezza automatica (carrozzeria 0.6% → specifiche tecniche 75-80%)
- **Post-processing**: Filtro efficace per valori vuoti in knowledge graph

## 📚 Documentazione

Vedi [progetto_log.md](notes/md/progetto_log.md) per la documentazione completa del processo di sviluppo.

## 🏁 Status

✅ **Completato**: Trasformazione CSV → Knowledge Graph  
🔄 **In Corso**: Import in GraphDB  
📋 **Prossimi**: Query avanzate, linking con knowledge base esterne

---

**Data progetto**: Gennaio 2026  
**Ambito**: Tesi di laurea - Web Semantico e Knowledge Graph