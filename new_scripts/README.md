# new_scripts - Versione 2 (Configurazione Dichiarativa di IRI)

## Descrizione

Questa cartella contiene una **seconda versione** dei script di generazione RDF che trasforma **literals selezionati in IRI** basandosi su una **configurazione dichiarativa** nel file `museum_mappings.py`.

## Principali Differenze dalla Versione 1

### Versione 1 (scripts/) - Approccio Entity Linking
- Usa entity linking con Wikidata API
- Solo alcuni attributi (brand, paese, tipo motore, etc.) diventano IRI
- Logica scritta nel codice Python
- Grafo con pochi nodi concettuali

### Versione 2 (new_scripts/) - Approccio Configurazione Dichiarativa
- **Configura quali predicati generano IRI dai loro valori literal**
- La lista è in `museum_mappings.py` (facile manutenzione)
- **Nessuna API call** - molto veloce
- **Crea un grafo completamente connesso**: ogni attributo configurato è un nodo IRI
- Ogni nodo può essere soggetto di ulteriori relazioni

## Come Funziona

### Tre Categorie di Predicati

Definite in `museum_mappings.py`:

1. **`literal_only_properties`**: Rimangono SEMPRE literal
   - Descrizione (rdfs:comment, TESTO)
   - Posizione nel museo (floorLevel, museumSection)
   - Inventory number (P217)

2. **`literal_value_to_iri_properties`**: I valori literal diventano IRI
   - P1002 (engine configuration)
   - P1028 (donated by)
   - P1559 (name in native language)
   - P2052 (speed)
   - P2109 (power)
   - P2754 (production date)
   - P516 (powered by)
   - P585 (point in time)
   - P8628 (displacement)
   - Schema.org: EnginePower, engineType, engineDisplacement, model, sponsor, dateVehicleFirstRegistered, etc.

3. **Tutto il resto**: Rimane literal per default

### Logica di Generazione

```python
if predicate in literal_only_properties:
    # Rimane literal: "1° Piano"
    → <vehicle> <predicate> "1° Piano"^^xsd:string
    
elif predicate in literal_value_to_iri_properties:
    # Diventa IRI: "posteriore 4 cilindri" → example.org/posteriore_4_cilindri
    → <vehicle> <predicate> <http://example.org/posteriore_4_cilindri>
    → <http://example.org/posteriore_4_cilindri> <rdf:type> <http://example.org/Attribute>
    → <http://example.org/posteriore_4_cilindri> <rdfs:label> "posteriore 4 cilindri"
    
else:
    # Di default rimane literal
    → <vehicle> <predicate> "valore"^^xsd:string
```

## Struttura dei File

```
new_scripts/
├── integrated_semantic_enricher.py    # MODIFICATO: Logica dichiarativa
├── museum_mappings.py                 # ⭐ MODIFICATO: Nuove liste
├── robust_wikidata_linker.py          # Copiato (non usato in V2)
├── extract_wikidata_attributes.py     # Copiato (non usato in V2)
└── README.md                          # (questo file)
```

## Come Usarla

### Esecuzione Diretta

```bash
cd c:\Users\salva\Desktop\Tesi\new_scripts
python integrated_semantic_enricher.py
```

### Uso Programmatico

```python
from integrated_semantic_enricher import AdvancedSemanticEnricherV2

enricher = AdvancedSemanticEnricherV2(
    use_wikidata_api=False,  # Non usa API
    convert_to_iris=True      # Usa configurazione museum_mappings
)

enricher.process_csv_to_rdf(
    csv_file="data/museo.csv",
    mapping_file="data/museum_column_mapping.csv",
    output_file="output/output_v2_all_iris.nt"
)
```

## Configurazione

### Aggiungere un nuovo predicato che genera IRI

Modifica `museum_mappings.py`:

```python
literal_value_to_iri_properties = [
    # ... predicati esistenti ...
    "http://www.wikidata.org/prop/direct/P9999",  # nuovo predicato
    "https://schema.org/newPredicate",            # nuovo predicato
]
```

### Aggiungere un predicato che rimane sempre literal

Modifica `museum_mappings.py`:

```python
literal_only_properties = [
    # ... predicati esistenti ...
    "http://example.org/newLiteral",  # rimane sempre literal
]
```

## Formato degli IRI

Usa il formato: `example.org/{attribute_name}_{normalized_value}`

### Esempi:
```
Valore original  : "posteriore 4 cilindri contrapposti"
Colonna          : "Motore" (P1002)
IRI generato     : http://example.org/posteriore_4_cilindri_contrapposti_raffreddato_ad_aria

Valore original  : "1131 cc"
Colonna          : "Cilindrata" (P8628)
IRI generato     : http://example.org/1131_cc

Valore original  : "Dono di Museo XYZ"
Colonna          : "Acquisizione" (P1028)
IRI generato     : http://example.org/dono_di_museo_xyz
```

## Triples Generati - Esempio

### Input CSV:
```
N. inventario: COM 004
Piano: 1° Piano
Sezione: Metamorfosi
Motore: posteriore 4 cilindri contrapposti raffreddato ad aria
Cilindrata: 1131 cc
Potenza: 25 CV a 3300 giri/min.
```

### Output RDF (N-Triples):
```turtle
# Literali che rimangono letterali (museo specifici)
<http://example.org/vehicle_COM_004> <http://example.org/floorLevel> "1° Piano"

<http://example.org/vehicle_COM_004> <http://example.org/museumSection> "Metamorfosi"

# Literali che diventano IRI (configurati in literal_value_to_iri_properties)
<http://example.org/vehicle_COM_004> <http://www.wikidata.org/prop/direct/P1002> <http://example.org/posteriore_4_cilindri_contrapposti_raffreddato_ad_aria>

<http://example.org/posteriore_4_cilindri_contrapposti_raffreddato_ad_aria> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://example.org/Attribute>

<http://example.org/posteriore_4_cilindri_contrapposti_raffreddato_ad_aria> <http://www.w3.org/2000/01/rdf-schema#label> "posteriore 4 cilindri contrapposti raffreddato ad aria"

<http://example.org/vehicle_COM_004> <http://www.wikidata.org/prop/direct/P8628> <http://example.org/1131_cc>

<http://example.org/1131_cc> <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://example.org/Attribute>

<http://example.org/1131_cc> <http://www.w3.org/2000/01/rdf-schema#label> "1131 cc"
```

## Vantaggi di Questo Approccio

✓ **Configurazione Dichiarativa**: No business logic nel codice  
✓ **Grafo Completamente Connesso**: Ogni attributo è un nodo indipendente  
✓ **Nodi come Soggetti**: Ogni attributo può avere proprietà ulteriori  
✓ **Facile Manutenzione**: Basta editare le liste in museum_mappings.py  
✓ **Veloce**: Nessuna API call, nessun entity linking  
✓ **Semantica Ricca**: Tripla aumentano significativamente  

## Confronto Con Versione 1

| Aspetto | V1 | V2 |
|---------|----|----|
| Entity Linking | Sì (Wikidata API) | No |
| Configurazione | Hardcoded nel codice | Dichiarativa (mappings) |
| Literals in IRI | Solo entità concettuali | Configurabile |
| Velocità | Lenta (API calls) | Veloce |
| Triple generate | ~500+ | ~1500+ |
| Nodi IRI | ~50 | ~300+ |

## File di Output

- **Versione 2**: `output/output_v2_all_iris.nt`
- **Formato**: N-Triples (.nt)
- **Encoding**: UTF-8

## Validazione

Verifica l'output con SPARQL:

```sparql
# Tutti i nodi Attribute
SELECT ?attr ?label WHERE {
  ?vehicle <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> 
           <https://schema.org/Vehicle> .
  ?vehicle ?predicate ?attr .
  ?attr <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> 
        <http://example.org/Attribute> .
  ?attr <http://www.w3.org/2000/01/rdf-schema#label> ?label .
}
LIMIT 20
```

---

**Data creazione**: Febbraio 2026  
**Versione**: V2.1 - Configurazione Dichiarativa
