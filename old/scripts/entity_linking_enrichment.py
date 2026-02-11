#!/usr/bin/env python3
"""
Script per l'arricchimento semantico tramite entity linking.
Trasforma entità brand, luoghi e persone da stringhe letterali in IRI strutturati
con rdf:type e rdfs:label, preferibilmente utilizzando Wikidata.
"""

import pandas as pd
import os
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, XSD
import re

# Definizione dei namespace
EX = Namespace("http://example.org/")
SCHEMA = Namespace("http://schema.org/")
WD = Namespace("http://www.wikidata.org/entity/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")

# Database di entity linking per brand automobilistici (espanso)
AUTOMOTIVE_BRANDS = {
    # Brand italiani
    "Fiat": {"wikidata_id": "Q27597", "type": WD.Q786820},
    "Ferrari": {"wikidata_id": "Q27586", "type": WD.Q786820},
    "Lancia": {"wikidata_id": "Q35886", "type": WD.Q786820},
    "Alfa Romeo": {"wikidata_id": "Q26921", "type": WD.Q786820}, 
    "Maserati": {"wikidata_id": "Q35962", "type": WD.Q786820},
    "Autobianchi": {"wikidata_id": "Q784873", "type": WD.Q786820},
    "Isotta Fraschini": {"wikidata_id": "Q640651", "type": WD.Q786820},
    "Itala": {"wikidata_id": "Q502768", "type": WD.Q786820},
    "Diatto": {"wikidata_id": "Q1209912", "type": WD.Q786820},
    "Spa": {"wikidata_id": "Q2301540", "type": WD.Q786820},  # Spa (car manufacturer)
    "Aquila Italiana": {"wikidata_id": "Q4782446", "type": WD.Q786820},
    "Cisitalia": {"wikidata_id": "Q917751", "type": WD.Q786820},
    "Storero": {"wikidata_id": "Q7620144", "type": WD.Q786820},
    
    # Brand francesi
    "Citroen": {"wikidata_id": "Q6746", "type": WD.Q786820},
    "Citroën": {"wikidata_id": "Q6746", "type": WD.Q786820},
    "Renault": {"wikidata_id": "Q6686", "type": WD.Q786820},
    "Peugeot": {"wikidata_id": "Q6742", "type": WD.Q786820},
    "Panhard": {"wikidata_id": "Q743224", "type": WD.Q786820},
    "Panhard & Levassor": {"wikidata_id": "Q743224", "type": WD.Q786820},
    "De Dion-Bouton": {"wikidata_id": "Q858039", "type": WD.Q786820},
    "De Dion Bouton": {"wikidata_id": "Q858039", "type": WD.Q786820},
    "Darracq": {"wikidata_id": "Q1166743", "type": WD.Q786820},
    "Clément-Panhard": {"wikidata_id": "Q2979712", "type": WD.Q786820},
    "Vinot & Deguingand": {"wikidata_id": "Q3558832", "type": WD.Q786820},
    "Hurtu": {"wikidata_id": "Q3143651", "type": WD.Q786820},
    "Bedelia": {"wikidata_id": "Q4879326", "type": WD.Q786820},
    
    # Brand tedeschi
    "Mercedes": {"wikidata_id": "Q36008", "type": WD.Q786820},
    "Mercedes Benz": {"wikidata_id": "Q36008", "type": WD.Q786820},
    "Mercedes-Benz": {"wikidata_id": "Q36008", "type": WD.Q786820}, 
    "BMW": {"wikidata_id": "Q26678", "type": WD.Q786820},
    "Benz": {"wikidata_id": "Q835203", "type": WD.Q786820},
    
    # Brand americani
    "Ford": {"wikidata_id": "Q44294", "type": WD.Q786820},
    "Cadillac": {"wikidata_id": "Q27856", "type": WD.Q786820},
    "Chevrolet": {"wikidata_id": "Q29570", "type": WD.Q786820},
    "Oldsmobile": {"wikidata_id": "Q30630", "type": WD.Q786820},
    "Stanley": {"wikidata_id": "Q1967513", "type": WD.Q786820},
    "Cord": {"wikidata_id": "Q1138918", "type": WD.Q786820},
    
    # Brand britannici
    "Rolls-Royce": {"wikidata_id": "Q34756", "type": WD.Q786820},
    "Bentley": {"wikidata_id": "Q27077", "type": WD.Q786820},
    "Jaguar": {"wikidata_id": "Q30055", "type": WD.Q786820},
    "Austin": {"wikidata_id": "Q852751", "type": WD.Q786820},
    
    # Altri brand
    "Bugatti": {"wikidata_id": "Q27038", "type": WD.Q786820},
    "Iso Rivolta": {"wikidata_id": "Q1676042", "type": WD.Q786820},
    "ACMA": {"wikidata_id": "Q4651134", "type": WD.Q786820}
}

# Database per luoghi (paesi/regioni)
PLACES = {
    "Italia": {
        "wikidata_id": "Q38",
        "type": WD.Q6256,  # country
    },
    "Francia": {
        "wikidata_id": "Q142", 
        "type": WD.Q6256,  # country
    },
    "Germania": {
        "wikidata_id": "Q183",
        "type": WD.Q6256,  # country
    },
    "Stati Uniti": {
        "wikidata_id": "Q30",
        "type": WD.Q6256,  # country
    },
    "Regno Unito": {
        "wikidata_id": "Q145",
        "type": WD.Q6256,  # country
    },
    "Giappone": {
        "wikidata_id": "Q17",
        "type": WD.Q6256,  # country
    },
    "Roma": {
        "wikidata_id": "Q220",
        "type": WD.Q515,  # city
    },
    "Milano": {
        "wikidata_id": "Q490",
        "type": WD.Q515,  # city
    },
    "Torino": {
        "wikidata_id": "Q495",
        "type": WD.Q515,  # city
    }
}

def create_entity_uri(wikidata_id):
    """Crea URI per un'entità Wikidata."""
    return WD[wikidata_id]

def normalize_brand_name(brand_name):
    """Normalizza il nome del brand per il matching migliorato."""
    if not brand_name:
        return None
    
    # Rimuovi caratteri speciali e normalizza
    normalized = brand_name.strip()
    
    # Gestione casi speciali e sinonimi
    normalized_lower = normalized.lower()
    
    # Normalizzazioni comuni
    if "citro" in normalized_lower:
        return "Citroen"
    elif "mercedes" in normalized_lower:
        return "Mercedes Benz"  # Unifica tutte le varianti Mercedes
    elif "de dion" in normalized_lower:
        return "De Dion-Bouton"
    elif "panhard" in normalized_lower and "special" not in normalized_lower:
        return "Panhard"
    elif "alfa" in normalized_lower and "romeo" in normalized_lower:
        return "Alfa Romeo"
    
    return normalized

def find_brand_fuzzy_match(brand_name, brands_database):
    """Trova match fuzzy per brand con variazioni nei nomi."""
    if not brand_name:
        return None
        
    normalized = normalize_brand_name(brand_name)
    normalized_lower = normalized.lower()
    
    # Match esatto
    if normalized in brands_database:
        return brands_database[normalized]
    
    # Match case-insensitive
    for key, info in brands_database.items():
        if key.lower() == normalized_lower:
            return info
    
    # Match parziale per brand compound o con variazioni
    for key, info in brands_database.items():
        key_lower = key.lower()
        # Cerca corrispondenze parziali (evita match troppo generici)
        if len(normalized_lower) > 3 and normalized_lower in key_lower:
            return info
        elif len(key_lower) > 3 and key_lower in normalized_lower:
            return info
    
    return None

def find_entity_info(value, entity_databases):
    """Trova informazioni sull'entità nei database disponibili con matching migliorato."""
    if not value:
        return None
    
    normalized_value = value.strip()
    
    # Cerca nei database forniti
    for db in entity_databases:
        # Se è il database dei brand, usa matching fuzzy
        if db == AUTOMOTIVE_BRANDS:
            fuzzy_result = find_brand_fuzzy_match(normalized_value, db)
            if fuzzy_result:
                return fuzzy_result
        else:
            # Per altri database, usa matching standard
            if normalized_value in db:
                return db[normalized_value]
            
            # Cerca con normalizzazione case-insensitive
            for key, info in db.items():
                if key.lower() == normalized_value.lower():
                    return info
    
    return None

def process_entity_linking(input_file, output_file):
    """
    Processa il file RDF per l'entity linking.
    Trasforma stringhe letterali in IRI strutturati per brand, luoghi e persone.
    """
    
    print("=== ARRICCHIMENTO SEMANTICO TRAMITE ENTITY LINKING ===")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print()
    
    if not os.path.exists(input_file):
        print(f"Errore: File {input_file} non trovato!")
        return False
    
    try:
        # Carica il grafo esistente
        print("Caricando grafo RDF esistente...")
        original_graph = Graph()
        original_graph.parse(input_file, format='nt')
        print(f"Grafo caricato: {len(original_graph)} triple")
        
        # Crea un nuovo grafo per l'output arricchito
        enriched_graph = Graph()
        
        # Copia tutti i namespace
        enriched_graph.bind("ex", EX)
        enriched_graph.bind("schema", SCHEMA)
        enriched_graph.bind("wdt", WDT)
        enriched_graph.bind("wd", WD)
        enriched_graph.bind("rdf", RDF)
        enriched_graph.bind("rdfs", RDFS)
        
        # Contatori
        linked_entities = 0
        brand_links = 0
        place_links = 0
        added_triples = 0
        
        print("Processando triple per entity linking...")
        
        # Processa ogni tripla del grafo originale
        for subject, predicate, obj in original_graph:
            
            # Copia la tripla originale
            enriched_graph.add((subject, predicate, obj))
            
            # Controlla se è una proprietà che può beneficiare di entity linking
            should_link = False
            entity_databases = []
            
            # Brand properties
            if (str(predicate) == "http://schema.org/brand" or 
                str(predicate) == "http://www.wikidata.org/prop/direct/P1716"):
                should_link = True
                entity_databases = [AUTOMOTIVE_BRANDS]
                
            # Country/place properties
            elif (str(predicate) == "http://schema.org/countryOfOrigin" or
                  str(predicate) == "http://www.wikidata.org/prop/direct/P1071" or
                  "location" in str(predicate).lower() or
                  "country" in str(predicate).lower()):
                should_link = True 
                entity_databases = [PLACES]
            
            # Se è una proprietà che richiede linking
            if should_link and isinstance(obj, Literal):
                entity_value = str(obj)
                entity_info = find_entity_info(entity_value, entity_databases)
                
                if entity_info:
                    # Crea URI per l'entità Wikidata
                    entity_uri = create_entity_uri(entity_info["wikidata_id"])
                    
                    # Sostituisce la tripla stringa con l'URI dell'entità
                    enriched_graph.remove((subject, predicate, obj))
                    enriched_graph.add((subject, predicate, entity_uri))
                    
                    # Aggiungi tipo e label all'entità Wikidata
                    # L'entità ha un tipo (es. car manufacturer/brand)
                    enriched_graph.add((entity_uri, RDF.type, entity_info["type"]))
                    # La label originale diventa rdfs:label dell'entità
                    enriched_graph.add((entity_uri, RDFS.label, Literal(entity_value, datatype=XSD.string)))
                    
                    linked_entities += 1
                    added_triples += 2
                    
                    # Conteggio per tipo
                    if entity_databases == [AUTOMOTIVE_BRANDS]:
                        brand_links += 1
                    elif entity_databases == [PLACES]:
                        place_links += 1
                    
                    # Stampa solo ogni 10 linking per ridurre verbosità
                    if linked_entities % 10 == 0:
                        print(f"  Processati {linked_entities} entity links...")
        
        # Salva il grafo arricchito
        print(f"\nSalvando grafo arricchito...")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        enriched_graph.serialize(destination=output_file, format='nt', encoding='utf-8')
        
        # Risultati finali
        print(f"\n=== RISULTATI ENTITY LINKING ===")
        print(f"Triple originali: {len(original_graph)}")
        print(f"Triple finali: {len(enriched_graph)}")
        print(f"Triple aggiunte: {added_triples}")
        print(f"Entità linkate: {linked_entities}")
        print(f"  - Brand automobilistici: {brand_links}")
        print(f"  - Luoghi (paesi/città): {place_links}")
        print(f"File salvato: {output_file}")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"Errore durante l'arricchimento: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def add_custom_entity(entity_name, wikidata_id, entity_type, database_name="custom"):
    """
    Aggiunge un'entità personalizzata ai database.
    
    Args:
        entity_name: Nome dell'entità come appare nei dati
        wikidata_id: ID Wikidata (es. "Q27597")
        entity_type: Tipo Wikidata (es. WD.Q786820 per car manufacturer)
        database_name: Nome del database ("brands", "places", o "custom")
    """
    
    entity_info = {
        "wikidata_id": wikidata_id,
        "type": entity_type
    }
    
    if database_name == "brands":
        AUTOMOTIVE_BRANDS[entity_name] = entity_info
    elif database_name == "places":
        PLACES[entity_name] = entity_info
    else:
        # Crea un database personalizzato se non esiste
        if not hasattr(add_custom_entity, 'custom_db'):
            add_custom_entity.custom_db = {}
        add_custom_entity.custom_db[entity_name] = entity_info
    
    print(f"Aggiunta entità personalizzata: {entity_name} → {wikidata_id}")

if __name__ == "__main__":
    # File di input e output
    input_file = "output/output_dual_mappings.nt" 
    output_file = "output/output_semantic_enriched.nt"
    
    # Esegui l'arricchimento semantico
    success = process_entity_linking(input_file, output_file)
    
    if success:
        print("\nArricchimento semantico completato con successo!")
    else:
        print("\nErrore nell'arricchimento semantico!")