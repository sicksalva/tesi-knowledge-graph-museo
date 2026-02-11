#!/usr/bin/env python3
"""
Script avanzato per l'arricchimento semantico con API Wikidata.
Trasforma il maggior numero possibile di stringhe in IRI utilizzando:
1. Database statico per entità comuni
2. API di Wikidata per entità non trovate
3. IRI personalizzati per dati molto frequenti
"""

import pandas as pd
import os
import requests
import time
import re
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, XSD
from urllib.parse import quote

# Definizione dei namespace
EX = Namespace("http://example.org/")
SCHEMA = Namespace("http://schema.org/")
WD = Namespace("http://www.wikidata.org/entity/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")

# Database statico espanso per brand automobilistici
AUTOMOTIVE_BRANDS = {
    "Fiat": {"wikidata_id": "Q27597", "type": WD.Q786820},
    "Ferrari": {"wikidata_id": "Q27586", "type": WD.Q786820},
    "Lancia": {"wikidata_id": "Q35886", "type": WD.Q786820},
    "Alfa Romeo": {"wikidata_id": "Q26921", "type": WD.Q786820},
    "Maserati": {"wikidata_id": "Q35962", "type": WD.Q786820},
    "Citroen": {"wikidata_id": "Q6746", "type": WD.Q786820},
    "Citroën": {"wikidata_id": "Q6746", "type": WD.Q786820},
    "Renault": {"wikidata_id": "Q6686", "type": WD.Q786820},
    "Peugeot": {"wikidata_id": "Q6742", "type": WD.Q786820},
    "Panhard": {"wikidata_id": "Q743224", "type": WD.Q786820},
    "Panhard & Levassor": {"wikidata_id": "Q743224", "type": WD.Q786820},
    "Iso Rivolta": {"wikidata_id": "Q1676042", "type": WD.Q786820},
    "Isotta Fraschini": {"wikidata_id": "Q640651", "type": WD.Q786820},
    "BMW": {"wikidata_id": "Q26678", "type": WD.Q786820},
    "Mercedes": {"wikidata_id": "Q36008", "type": WD.Q786820},
    "Mercedes-Benz": {"wikidata_id": "Q36008", "type": WD.Q786820},
    "Ford": {"wikidata_id": "Q44294", "type": WD.Q786820},
    "Rolls-Royce": {"wikidata_id": "Q34756", "type": WD.Q786820},
    "Bentley": {"wikidata_id": "Q27077", "type": WD.Q786820},
    "Jaguar": {"wikidata_id": "Q30055", "type": WD.Q786820},
    "Austin": {"wikidata_id": "Q852751", "type": WD.Q786820},
    "Bugatti": {"wikidata_id": "Q27038", "type": WD.Q786820},
    "Cadillac": {"wikidata_id": "Q27856", "type": WD.Q786820},
    "Chevrolet": {"wikidata_id": "Q29570", "type": WD.Q786820},
    "De Dion-Bouton": {"wikidata_id": "Q858039", "type": WD.Q786820},
    "Stanley": {"wikidata_id": "Q1967513", "type": WD.Q786820},
    "Autobianchi": {"wikidata_id": "Q784873", "type": WD.Q786820},
    "Benz": {"wikidata_id": "Q835203", "type": WD.Q786820},
    "ACMA": {"wikidata_id": "Q4651134", "type": WD.Q786820}  # ACMA Vespa
}

# Database per luoghi/paesi
PLACES = {
    "Italia": {"wikidata_id": "Q38", "type": WD.Q6256},
    "Francia": {"wikidata_id": "Q142", "type": WD.Q6256},
    "Germania": {"wikidata_id": "Q183", "type": WD.Q6256},
    "Stati Uniti": {"wikidata_id": "Q30", "type": WD.Q6256},
    "Regno Unito": {"wikidata_id": "Q145", "type": WD.Q6256},
    "Giappone": {"wikidata_id": "Q17", "type": WD.Q6256},
    "Spagna": {"wikidata_id": "Q29", "type": WD.Q6256},
    "Belgio": {"wikidata_id": "Q31", "type": WD.Q6256},
    "Svizzera": {"wikidata_id": "Q39", "type": WD.Q6256},
    "Austria": {"wikidata_id": "Q40", "type": WD.Q6256},
    "Olanda": {"wikidata_id": "Q55", "type": WD.Q6256},
    "Paesi Bassi": {"wikidata_id": "Q55", "type": WD.Q6256},
    "Svezia": {"wikidata_id": "Q34", "type": WD.Q6256},
    # Città
    "Roma": {"wikidata_id": "Q220", "type": WD.Q515},
    "Milano": {"wikidata_id": "Q490", "type": WD.Q515},
    "Torino": {"wikidata_id": "Q495", "type": WD.Q515},
    "Parigi": {"wikidata_id": "Q90", "type": WD.Q515},
    "Londra": {"wikidata_id": "Q84", "type": WD.Q515},
    "Berlino": {"wikidata_id": "Q64", "type": WD.Q515}
}

# Database per tipi di motore e tecnologie
TECHNICAL_TERMS = {
    "elettrico": {"iri": EX["electric_motor"], "type": EX["EngineType"]},
    "benzina": {"iri": EX["gasoline_engine"], "type": EX["EngineType"]},  
    "gasolio": {"iri": EX["diesel_engine"], "type": EX["EngineType"]},
    "vapore": {"iri": EX["steam_engine"], "type": EX["EngineType"]},
    "ibrido": {"iri": EX["hybrid_engine"], "type": EX["EngineType"]},
    "combustione interna": {"iri": EX["internal_combustion_engine"], "type": EX["EngineType"]},
    
    # Trasmissioni
    "manuale": {"iri": EX["manual_transmission"], "type": EX["TransmissionType"]},
    "automatico": {"iri": EX["automatic_transmission"], "type": EX["TransmissionType"]},
    "semiautomatico": {"iri": EX["semiautomatic_transmission"], "type": EX["TransmissionType"]},
    
    # Tipi di trazione  
    "anteriore": {"iri": EX["front_wheel_drive"], "type": EX["DriveType"]},
    "posteriore": {"iri": EX["rear_wheel_drive"], "type": EX["DriveType"]},
    "integrale": {"iri": EX["all_wheel_drive"], "type": EX["DriveType"]},
    
    # Carrozzeria
    "spider": {"iri": EX["convertible"], "type": EX["BodyStyle"]},
    "coupé": {"iri": EX["coupe"], "type": EX["BodyStyle"]},
    "berlina": {"iri": EX["sedan"], "type": EX["BodyStyle"]},
    "station wagon": {"iri": EX["station_wagon"], "type": EX["BodyStyle"]},
    "hatchback": {"iri": EX["hatchback"], "type": EX["BodyStyle"]}
}

class WikidataAPI:
    """Classe per interagire con l'API di Wikidata"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MuseoAutoArricchimento/1.0 (mailto:contatto@example.com)'
        })
        self.cache = {}  # Cache per evitare richieste duplicate
        
    def search_entity(self, term, entity_type="item", language="it", limit=5):
        """
        Cerca un'entità su Wikidata utilizzando la API di ricerca.
        
        Args:
            term: Termine da cercare
            entity_type: Tipo di entità ("item" per default)
            language: Lingua per la ricerca
            limit: Numero massimo di risultati
            
        Returns:
            Lista di risultati con ID Wikidata e informazioni
        """
        if term in self.cache:
            return self.cache[term]
            
        try:
            # URL per la ricerca
            search_url = "https://www.wikidata.org/w/api.php"
            params = {
                'action': 'wbsearchentities',
                'search': term,
                'language': language,
                'type': entity_type,
                'limit': limit,
                'format': 'json'
            }
            
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get('search', []):
                result = {
                    'id': item.get('id'),
                    'label': item.get('label'),
                    'description': item.get('description', ''),
                    'url': item.get('concepturi')
                }
                results.append(result)
            
            # Aggiungi alla cache
            self.cache[term] = results
            
            # Piccola pausa per essere gentili con l'API
            time.sleep(0.1)
            
            return results
            
        except Exception as e:
            print(f"Errore nella ricerca Wikidata per '{term}': {str(e)}")
            return []
    
    def get_entity_details(self, entity_id):
        """
        Ottiene dettagli di un'entità specifica da Wikidata.
        
        Args:
            entity_id: ID dell'entità (es. "Q27597")
            
        Returns:
            Dizionario con le informazioni dell'entità
        """
        if f"details_{entity_id}" in self.cache:
            return self.cache[f"details_{entity_id}"]
            
        try:
            url = "https://www.wikidata.org/w/api.php"
            params = {
                'action': 'wbgetentities',
                'ids': entity_id,
                'format': 'json',
                'languages': 'it|en'
            }
            
            response = self.session.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            entity = data.get('entities', {}).get(entity_id, {})
            
            # Estrai informazioni utili
            details = {
                'id': entity_id,
                'labels': entity.get('labels', {}),
                'descriptions': entity.get('descriptions', {}),
                'claims': entity.get('claims', {})
            }
            
            # Cache del risultato
            self.cache[f"details_{entity_id}"] = details
            
            time.sleep(0.1)
            return details
            
        except Exception as e:
            print(f"Errore nell'ottenere dettagli per {entity_id}: {str(e)}")
            return None

def find_entity_info_advanced(value, entity_databases, wikidata_api, should_use_wikidata=True):
    """
    Trova informazioni sull'entità usando database statici e API Wikidata.
    
    Args:
        value: Valore da cercare  
        entity_databases: Lista di database statici
        wikidata_api: Istanza dell'API Wikidata
        should_use_wikidata: Se usare Wikidata per entità non trovate
        
    Returns:
        Dizionario con informazioni dell'entità o None
    """
    if not value:
        return None
        
    normalized_value = value.strip()
    
    # 1. Cerca nei database statici prima
    for db in entity_databases:
        if normalized_value in db:
            return db[normalized_value]
            
        # Cerca con normalizzazione case-insensitive
        for key, info in db.items():
            if key.lower() == normalized_value.lower():
                return info
    
    # 2. Se non trovato e abilitato, usa Wikidata API
    if should_use_wikidata and wikidata_api:
        print(f"Cercando su Wikidata: '{normalized_value}'")
        
        # Cerca su Wikidata
        search_results = wikidata_api.search_entity(normalized_value)
        
        if search_results:
            # Prendi il primo risultato (più rilevante)
            best_result = search_results[0]
            
            # Ottieni dettagli dell'entità
            details = wikidata_api.get_entity_details(best_result['id'])
            
            if details:
                # Determina il tipo dell'entità basandosi sui claims
                entity_type = WD.Q35120  # Default: entity
                
                # Cerca claim specifici per determinare il tipo
                claims = details.get('claims', {})
                if 'P31' in claims:  # "instance of"
                    instance_of = claims['P31']
                    if instance_of:
                        # Cerca tipi specifici
                        for claim in instance_of:
                            mainsnak = claim.get('mainsnak', {})
                            datavalue = mainsnak.get('datavalue', {})
                            value_data = datavalue.get('value', {})
                            qid = value_data.get('id', '')
                            
                            # Mappa tipi comuni
                            if qid in ['Q786820', 'Q936518']:  # car manufacturer, car model
                                entity_type = WD.Q786820
                                break
                            elif qid in ['Q6256', 'Q3624078']:  # country, sovereign state
                                entity_type = WD.Q6256
                                break
                            elif qid in ['Q515']:  # city
                                entity_type = WD.Q515
                                break
                
                result = {
                    'wikidata_id': best_result['id'],
                    'type': entity_type,
                    'source': 'wikidata_api',
                    'confidence': 0.8  # Fiducia media per risultati API
                }
                
                print(f"  ✓ Trovato: {best_result['label']} ({best_result['id']})")
                return result
    
    return None

def create_custom_iri_for_frequent_data(value, property_type):
    """
    Crea IRI personalizzati per dati molto frequenti.
    
    Args:
        value: Valore del dato
        property_type: Tipo di proprietà (per categorizzare)
        
    Returns:
        Dizionario con IRI e tipo personalizzato
    """
    # Normalizza il valore per l'IRI
    normalized = re.sub(r'[^a-zA-Z0-9\s]', '', value)
    normalized = re.sub(r'\s+', '_', normalized.strip()).lower()
    
    # Crea IRI basato sul tipo di proprietà
    if 'potenza' in property_type.lower() or 'power' in property_type.lower():
        return {
            'iri': EX[f"power_rating_{normalized}"],
            'type': EX["PowerRating"],
            'value': value
        }
    elif 'cilindrata' in property_type.lower() or 'displacement' in property_type.lower():
        return {
            'iri': EX[f"engine_displacement_{normalized}"],
            'type': EX["EngineDisplacement"],
            'value': value
        }
    elif 'velocit' in property_type.lower() or 'speed' in property_type.lower():
        return {
            'iri': EX[f"max_speed_{normalized}"],
            'type': EX["MaxSpeed"],
            'value': value
        }
    elif 'anno' in property_type.lower() or 'year' in property_type.lower():
        return {
            'iri': EX[f"year_{normalized}"],
            'type': EX["Year"],
            'value': value
        }
    else:
        return {
            'iri': EX[f"custom_value_{normalized}"],
            'type': EX["CustomValue"],
            'value': value
        }

def should_create_iri_for_value(value, predicate_str):
    """
    Determina se un valore dovrebbe essere trasformato in IRI personalizzato.
    
    Args:
        value: Valore da valutare
        predicate_str: Stringa del predicato per capire il contesto
        
    Returns:
        Bool indicante se creare un IRI personalizzato
    """
    if not value or len(str(value).strip()) < 2:
        return False
        
    # Trasforma in IRI se:
    # 1. Contiene unità di misura comuni
    if re.search(r'\b(CV|hp|HP|cc|km/h|mph|l/100|kg|mm|cm|m)\b', value):
        return True
    
    # 2. È un anno (4 cifre)
    if re.match(r'^\d{4}$', str(value).strip()):
        return True
        
    # 3. È un valore tecnico frequente
    technical_keywords = ['cilindri', 'marce', 'tempi', 'valvole', 'porte']
    if any(keyword in value.lower() for keyword in technical_keywords):
        return True
        
    # 4. È una proprietà P di Wikidata (es. P2109)
    if re.match(r'^P\d+', str(value).strip()):
        return True
        
    return False

def process_advanced_entity_linking(input_file, output_file, use_wikidata_api=True):
    """
    Processa il file RDF per l'entity linking avanzato utilizzando:
    1. Database statici
    2. API Wikidata 
    3. IRI personalizzati per dati frequenti
    """
    
    print("=== ARRICCHIMENTO SEMANTICO AVANZATO ===")
    print(f"Input: {input_file}")
    print(f"Output: {output_file}")
    print(f"API Wikidata: {'Attiva' if use_wikidata_api else 'Disattivata'}")
    print()
    
    if not os.path.exists(input_file):
        print(f"Errore: File {input_file} non trovato!")
        return False
    
    try:
        # Inizializza API Wikidata
        wikidata_api = WikidataAPI() if use_wikidata_api else None
        
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
        processed_triples = 0
        static_links = 0
        wikidata_api_links = 0
        custom_iris = 0
        added_triples = 0
        
        print("Processando triple per entity linking avanzato...")
        
        # Processa ogni tripla del grafo originale
        for subject, predicate, obj in original_graph:
            processed_triples += 1
            
            # Copia la tripla originale (per ora)
            enriched_graph.add((subject, predicate, obj))
            
            # Controlla se è una proprietà che può beneficiare di entity linking
            should_link = False
            entity_databases = []
            predicate_str = str(predicate)
            
            # Brand properties
            if (predicate_str in ["http://schema.org/brand", "http://www.wikidata.org/prop/direct/P1716"]):
                should_link = True
                entity_databases = [AUTOMOTIVE_BRANDS]
                
            # Country/place properties
            elif (predicate_str in ["http://schema.org/countryOfOrigin", "http://www.wikidata.org/prop/direct/P1071"] or
                  "location" in predicate_str.lower() or "country" in predicate_str.lower()):
                should_link = True 
                entity_databases = [PLACES]
                
            # Technical properties (motore, trasmissione, etc.)
            elif (predicate_str in ["http://schema.org/engineType", "http://schema.org/vehicleTransmission"] or
                  any(term in predicate_str.lower() for term in ["engine", "transmission", "fuel", "motor", "cambio"])):
                should_link = True
                entity_databases = [TECHNICAL_TERMS]
            
            # Se è una proprietà che richiede linking e è un Literal
            if should_link and isinstance(obj, Literal):
                entity_value = str(obj)
                entity_info = find_entity_info_advanced(
                    entity_value, entity_databases, wikidata_api, use_wikidata_api
                )
                
                if entity_info:
                    # Rimuovi la tripla originale
                    enriched_graph.remove((subject, predicate, obj))
                    
                    if 'source' in entity_info and entity_info['source'] == 'wikidata_api':
                        # Risultato da API Wikidata
                        entity_uri = WD[entity_info["wikidata_id"]]
                        enriched_graph.add((subject, predicate, entity_uri))
                        enriched_graph.add((entity_uri, RDF.type, entity_info["type"]))
                        enriched_graph.add((entity_uri, RDFS.label, Literal(entity_value, datatype=XSD.string)))
                        wikidata_api_links += 1
                        added_triples += 2
                        
                    elif 'iri' in entity_info:
                        # Risultato da database tecnici (IRI personalizzati)
                        entity_uri = entity_info["iri"]
                        enriched_graph.add((subject, predicate, entity_uri))
                        enriched_graph.add((entity_uri, RDF.type, entity_info["type"]))
                        enriched_graph.add((entity_uri, RDFS.label, Literal(entity_value, datatype=XSD.string)))
                        custom_iris += 1
                        added_triples += 2
                        
                    else:
                        # Risultato da database statico Wikidata
                        entity_uri = WD[entity_info["wikidata_id"]]
                        enriched_graph.add((subject, predicate, entity_uri))
                        enriched_graph.add((entity_uri, RDF.type, entity_info["type"]))
                        enriched_graph.add((entity_uri, RDFS.label, Literal(entity_value, datatype=XSD.string)))
                        static_links += 1
                        added_triples += 2
                        
            # Se non mappato ma può beneficiare di IRI personalizzato
            elif isinstance(obj, Literal) and should_create_iri_for_value(str(obj), predicate_str):
                entity_value = str(obj)
                custom_info = create_custom_iri_for_frequent_data(entity_value, predicate_str)
                
                if custom_info:
                    # Rimuovi la tripla originale e aggiungi quella con IRI
                    enriched_graph.remove((subject, predicate, obj))
                    enriched_graph.add((subject, predicate, custom_info["iri"]))
                    enriched_graph.add((custom_info["iri"], RDF.type, custom_info["type"]))
                    enriched_graph.add((custom_info["iri"], RDFS.label, Literal(entity_value, datatype=XSD.string)))
                    custom_iris += 1
                    added_triples += 2
            
            # Progress ogni 100 triple
            if processed_triples % 100 == 0:
                print(f"  Processate {processed_triples} triple...")
        
        # Salva il grafo arricchito
        print(f"\nSalvando grafo arricchito...")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        enriched_graph.serialize(destination=output_file, format='nt', encoding='utf-8')
        
        # Risultati finali
        print(f"\n=== RISULTATI ARRICCHIMENTO AVANZATO ===")
        print(f"Triple originali: {len(original_graph)}")
        print(f"Triple finali: {len(enriched_graph)}")
        print(f"Triple aggiunte: {added_triples}")
        print(f"Entity linking totali: {static_links + wikidata_api_links + custom_iris}")
        print(f"  - Database statico: {static_links}")
        print(f"  - API Wikidata: {wikidata_api_links}")
        print(f"  - IRI personalizzati: {custom_iris}")
        print(f"File salvato: {output_file}")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"Errore durante l'arricchimento avanzato: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # File di input e output
    input_file = "output/output_dual_mappings.nt" 
    output_file = "output/output_advanced_semantic_enriched.nt"
    
    # Esegui l'arricchimento semantico avanzato
    success = process_advanced_entity_linking(input_file, output_file, use_wikidata_api=True)
    
    if success:
        print("\nArricchimento semantico avanzato completato con successo!")
    else:
        print("\nErrore nell'arricchimento semantico avanzato!")