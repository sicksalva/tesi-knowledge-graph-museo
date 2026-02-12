#!/usr/bin/env python3
"""
Sistema integrato per generazione RDF con arricchimento semantico avanzato.

Questo sistema legge direttamente da museo.csv e genera un grafo RDF applicando:
1. Mappings da museum_column_mapping.csv per determinare i predicati
2. Logica da museum_mappings.py per decidere se creare IRI o literal
3. Entity linking robusto con API Wikidata per entità concettuali
4. Normalizzazione di valori tecnici (potenza, cilindrata, velocità)
5. IRI personalizzati per concetti riutilizzabili

IMPORTANTE: Tutta la logica hardcoded è stata spostata in museum_mappings.py.
Questo file contiene SOLO la logica di:
- Lettura CSV e generazione RDF
- Chiamate API Wikidata
- Cache delle entità risolte
- Coordinamento del processo di arricchimento
"""

import sys
import os
import csv
import pandas as pd
import glob
from typing import Dict, Optional, List
# Aggiungi la directory scripts al path per importare il linker E i mappings
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from robust_wikidata_linker import WikidataEntityLinker
import museum_mappings  # Importa i mappings personalizzati
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, XSD
import re

# Namespace
EX = Namespace("http://example.org/")
SCHEMA = Namespace("https://schema.org/")  # HTTPS per Schema.org
WD = Namespace("http://www.wikidata.org/entity/")
WDT = Namespace("http://www.wikidata.org/prop/direct/")

class AdvancedSemanticEnricher:
    """
    Sistema avanzato di arricchimento semantico che combina:
    - Entity linking robusto con Wikidata API
    - Normalizzazione valori tecnici
    - IRI personalizzati
    """
    
    def __init__(self, use_wikidata_api=True, cache_file="advanced_enricher_cache.pkl"):
        self.wikidata_linker = WikidataEntityLinker(cache_file=cache_file) if use_wikidata_api else None
        self.use_wikidata_api = use_wikidata_api
        
        # Cache dinamico entità risolte (si espande automaticamente)
        self.entity_cache_file = cache_file.replace('.pkl', '_entities.json') if cache_file else 'entity_cache.json'
        self.entity_cache = self._load_entity_cache()
        
        print(f"Cache entità caricato: {len(self.entity_cache)} entità precedentemente risolte")
    
    def split_entities(self, value: str):
        """
        Divide valori con più entità (persone, designer, etc.) separati da connettori.
        """
        import re
        # divide su virgole, " e ", "&", ";", "/", "per", e A CAPO
        parts = re.split(r'\s*(?:,| e | & |;|/|\bper\b|\n)\s*', value)
        # pulisce spazi vuoti e rimuove parti troppo corte o generiche
        entities = []
        for p in parts:
            p = p.strip()
            # Skip parti vuote, troppo corte o generiche
            if (p and len(p) > 3 and 
                not re.match(r'^(di|da|per|con|in|su|a|il|la|le|lo|gli|un|una|dei|delle|dello|della)$', p.lower()) and
                not re.match(r'^[A-Z]+$', p)):  # Skip acronimi semplici
                entities.append(p)
        return entities
    
    def enrich_single_value(self, value: str, predicate_str: str) -> Dict:
        """
        Arricchisce un singolo valore usando tutte le strategie disponibili.
        """
        if not value or not isinstance(value, str):
            return {'action': 'keep_original', 'value': value}
        
        # 0.1 NUOVO: Ignora completamente descrizioni lunghe - NON DEVONO DIVENTARE IRI
        if museum_mappings.is_long_description(value):
            return {'action': 'keep_original', 'value': value}
        
        # 0.2 PRIORITÀ ASSOLUTA: ANNI DEVONO RIMANERE LITERAL - CONTROLLO ESPLICITO
        if museum_mappings.is_year_value(value):
            return {'action': 'keep_original', 'value': value}
        
        # 0.3. USA I MAPPINGS per determinare se il predicato deve rimanere literal
        if self._should_keep_literal_by_mapping(predicate_str):
            return {'action': 'keep_original', 'value': value}

        # 1. NON CREARE IRI TECNICI - cilindrata, potenza, velocità rimangono LITERAL
        # (La normalizzazione tecnica è disabilitata - questi dati devono essere literal)
        
        # 2. Entity linking automatico SOLO per proprietà che devono essere IRI (guidato da mappings)
        if self._should_create_iri_by_mapping(predicate_str):
            
            # NUOVO: Gestione multiple entità (persone, designer, etc.)
            if museum_mappings.is_multiple_entities_predicate(predicate_str):
                entities = self.split_entities(value)
                if len(entities) > 1:
                    # Multiple entità trovate - processale separatamente
                    entity_results = []
                    for entity_name in entities:
                        entity_result = self._process_single_entity(entity_name, predicate_str)
                        if entity_result:
                            entity_results.append(entity_result)
                    
                    if entity_results:
                        return {
                            'action': 'create_multiple_entities', 
                            'original_value': value,
                            'entities': entity_results
                        }
            
            # Processo singola entità (logica originale)
            single_result = self._process_single_entity(value, predicate_str)
            if single_result:
                return single_result
        
        # 3. NON creare custom IRI - se non trovato su Wikidata, resta literal
        # Gli unici custom IRI sono i veicoli (subject)
        
        # 4. Mantieni originale
        return {'action': 'keep_original', 'value': value}
    
    def _process_single_entity(self, value: str, predicate_str: str):
        """
        Processa singola entità - logica estratta dal metodo principale.
        """
        # Prima controlla cache dinamico
        cached_result = self._check_entity_cache(value)
        if cached_result:
            return {
                'action': 'create_wikidata_iri',
                'original_value': value,
                'iri': WD[cached_result['qid']],
                'rdf_type': WD[cached_result['type']],  # Usa il tipo dal cache 
                'source': 'dynamic_cache',
                'confidence': cached_result.get('confidence', 1.0)
            }
        
        # Se non in cache, usa API Wikidata
        if self.wikidata_linker:
            # Determina tipo suggerito dai mappings
            entity_type = museum_mappings.get_entity_type_for_predicate(predicate_str)
            
            # Chiama API con confidence più alta per evitare falsi positivi
            api_result = self.wikidata_linker.find_best_entity(value, min_confidence=0.6)
            if api_result:
                
                # Salva in cache dinamico per future ricerche
                self._save_to_entity_cache(value, api_result['qid'], entity_type, api_result['confidence'])
                
                return {
                    'action': 'create_wikidata_iri',
                    'original_value': value,
                    'iri': WD[api_result['qid']],
                    'rdf_type': WD[entity_type],
                    'source': 'wikidata_api_new',
                    'confidence': api_result['confidence']
                }
        
        return None
    
    def _load_entity_cache(self):
        """Carica cache dinamico delle entità risolte."""
        import json
        try:
            if os.path.exists(self.entity_cache_file):
                with open(self.entity_cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Impossibile caricare cache entità: {e}")
        return {}
    
    def _check_entity_cache(self, value: str):
        """Controlla se valore è già risolto in cache."""
        normalized = value.strip().lower()
        return self.entity_cache.get(normalized)
    
    def _save_to_entity_cache(self, value: str, qid: str, entity_type: str, confidence: float):
        """Salva risultato in cache dinamico (si espande automaticamente)."""
        import json
        normalized = value.strip().lower()
        
        self.entity_cache[normalized] = {
            'qid': qid,
            'type': entity_type,
            'confidence': confidence,
            'original_value': value
        }
        
        # Salva su disco immediatamente
        try:
            with open(self.entity_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.entity_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Impossibile salvare cache entità: {e}")
    
    def _should_create_custom_iri(self, value: str, predicate_str: str) -> bool:
        """
        Determina se creare IRI personalizzato usando SOLO i mappings.
        Niente logica hardcoded - se non è nei mappings, non lo facciamo.
        """
        if not value or len(value.strip()) < 2:
            return False
        
        # Prima controlla se è nei literal_only (priorità assoluta)
        if self._should_keep_literal_by_mapping(predicate_str):
            return False  # Deve rimanere literal
        
        # Se non è esplicitamente nei target IRI dei mappings, non creare custom IRI
        if not self._should_create_iri_by_mapping(predicate_str):
            return False
        
        # Se siamo qui, il mapping dice che dovrebbe essere IRI
        # ma l'API non ha trovato nulla, quindi creiamo custom IRI
        return True
    
    def _should_keep_literal_by_mapping(self, predicate_str: str) -> bool:
        """
        Usa i mappings del museo per determinare se mantenere literal.
        """
        return predicate_str in museum_mappings.literal_only_properties
    
    def _should_create_iri_by_mapping(self, predicate_str: str) -> bool:
        """
        Usa i mappings del museo per determinare se creare IRI.
        """
        return predicate_str in museum_mappings.iri_target_properties
    

    
    def _create_custom_iri(self, value: str, predicate_str: str) -> URIRef:
        """Crea IRI personalizzato SOLO per concetti riutilizzabili (non anni/dati numerici)."""
        # Normalizza per IRI
        normalized = re.sub(r'[^a-zA-Z0-9\s]', '', value)
        normalized = re.sub(r'\s+', '_', normalized.strip()).lower()
        
        # Prefisso basato sul tipo concettuale (delegato ai mappings)
        prefix = museum_mappings.get_custom_iri_prefix(predicate_str)
        
        return EX[f"{prefix}_{normalized}"]
    
    def _load_column_mappings(self, mapping_file: str) -> Dict[str, Dict]:
        """Carica mappings colonne CSV -> proprietà RDF."""
        mappings = {}
        try:
            df = pd.read_csv(mapping_file, encoding='utf-8')
            for _, row in df.iterrows():
                col_name = row['column_name']
                wd_prop = row['wikidata_property']
                
                # Determina URI completo del predicato Wikidata
                if wd_prop.startswith('P') and len(wd_prop) <= 6:
                    # Proprietà Wikidata
                    predicate_uri = f"http://www.wikidata.org/prop/direct/{wd_prop}"
                elif wd_prop.startswith('custom:'):
                    # Proprietà custom
                    custom_name = wd_prop.replace('custom:', '')
                    predicate_uri = f"http://example.org/{custom_name}"
                else:
                    predicate_uri = wd_prop
                
                mappings[col_name] = {
                    'predicate': predicate_uri,
                    'property_id': wd_prop,
                    'label': row['property_label'],
                    'category': row['macro_category'],
                    'schema_predicates': []  # Sarà popolato da mappings.csv
                }
            
            print(f"Caricati {len(mappings)} mappings colonne")
            return mappings
        except Exception as e:
            print(f"Errore caricamento mappings: {e}")
            return {}
    
    def _load_schema_mappings(self, mappings_file: str, column_mappings: Dict) -> Dict[str, Dict]:
        """Carica mappings aggiuntivi da mappings.csv (Schema.org, etc.)."""
        try:
            df = pd.read_csv(mappings_file, encoding='utf-8')
            schema_count = 0
            
            for _, row in df.iterrows():
                # La colonna 'Source' contiene URI come 'http://sparql.xyz/facade-x/data/Marca'
                source = row.get('Source', '')
                if pd.isna(source) or source == '':
                    continue
                
                # Estrai il nome della colonna dal Source URI
                # Es: 'http://sparql.xyz/facade-x/data/Marca' -> 'Marca'
                if '/data/' in source:
                    col_name_encoded = source.split('/data/')[-1]
                    # Decodifica URL encoding (es: %2520 -> spazio)
                    import urllib.parse
                    col_name = urllib.parse.unquote(col_name_encoded).replace('%20', ' ')
                    
                    # Trova match nelle colonne mappate
                    matched_col = None
                    for mapped_col in column_mappings.keys():
                        if col_name.lower() == mapped_col.lower() or \
                           col_name.replace('_', ' ').lower() == mapped_col.lower():
                            matched_col = mapped_col
                            break
                    
                    if matched_col:
                        # Estrai predicati Schema.org da varie colonne
                        schema_props = []
                        
                        # Controlla colonna Schema.org
                        schema_org = row.get('Schema.org', '')
                        if not pd.isna(schema_org) and schema_org.strip() != '':
                            schema_props.append(schema_org.strip())
                        
                        # Controlla anche Option 1, 2, 3, 4 (colonne alternate)
                        for i in [1, 2, 3, 4]:
                            opt = row.get(f'Option {i}', '')
                            if not pd.isna(opt) and opt.strip() != '':
                                schema_props.append(opt.strip())
                        
                        # Valida e aggiungi solo predicati validi
                        for schema_prop in schema_props:
                            # Valida: non deve contenere virgole, numeri all'inizio, spazi multipli
                            if self._is_valid_predicate(schema_prop):
                                # Costruisci URI completo Schema.org (sempre HTTPS)
                                if schema_prop.startswith('http://schema.org/'):
                                    schema_uri = schema_prop.replace('http://', 'https://')
                                elif schema_prop.startswith('https://schema.org/'):
                                    schema_uri = schema_prop
                                elif schema_prop.startswith('http'):
                                    schema_uri = schema_prop
                                else:
                                    schema_uri = f"https://schema.org/{schema_prop}"
                                
                                # Aggiungi a column_mappings (evita duplicati)
                                if schema_uri not in column_mappings[matched_col]['schema_predicates']:
                                    column_mappings[matched_col]['schema_predicates'].append(schema_uri)
                                    schema_count += 1
            
            print(f"Aggiunti {schema_count} mappings Schema.org per interoperabilità")
            return column_mappings
            
        except Exception as e:
            print(f"Warning: Impossibile caricare mappings.csv: {e}")
            return column_mappings
    
    def _is_valid_predicate(self, value: str) -> bool:
        """Valida se un valore sembra essere un predicato valido."""
        if not value or len(value) < 3:
            return False
        
        value = value.strip()
        
        # Esclude valori che sembrano dati invece di predicati
        # Se contiene virgola, è probabilmente una lista di valori
        if ',' in value:
            return False
        
        # Se inizia con numero seguito da spazio, è probabilmente un valore
        # Es: "3 differenziali", "4 ruote motrici"
        if re.match(r'^\d+\s', value):
            return False
        
        # Se contiene più di 2 spazi, è probabilmente una frase/descrizione
        if value.count(' ') > 2:
            return False
        
        # Se è un URL completo, è valido
        if value.startswith('http://') or value.startswith('https://'):
            return True
        
        # Altrimenti deve essere un identificatore camelCase o snake_case
        # Es: "brand", "engineType", "numberOfForwardGears", "AllWheelDriveConfiguration"
        if re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', value):
            return True
        
        return False
    
    def _create_subject_iri(self, inventory_number: str) -> URIRef:
        """Crea IRI per subject (veicolo) basato su numero inventario."""
        # Normalizza numero inventario per IRI
        normalized = re.sub(r'[^a-zA-Z0-9]', '_', inventory_number.strip())
        return EX[f"vehicle_{normalized}"]
    
    def process_csv_to_rdf(self, csv_file: str, mapping_file: str, output_file: str) -> bool:
        """
        Processa CSV museo generando RDF con entity linking e arricchimento semantico.
        """
        
        print("=== GENERAZIONE RDF CON ENTITY LINKING ===")
        print(f"Input CSV: {csv_file}")
        print(f"Mappings: {mapping_file}")
        print(f"Output: {output_file}")
        print(f"Wikidata API: {'Attiva' if self.use_wikidata_api else 'Disattivata'}")
        print()
        
        if not os.path.exists(csv_file):
            print(f"Errore: File {csv_file} non trovato!")
            return False
        
        if not os.path.exists(mapping_file):
            print(f"Errore: File {mapping_file} non trovato!")
            return False
        
        try:
            # Carica mappings colonne
            column_mappings = self._load_column_mappings(mapping_file)
            if not column_mappings:
                print("Errore: Nessun mapping caricato!")
                return False
            
            # Carica mappings Schema.org aggiuntivi da mappings.csv
            mappings_csv = os.path.join(os.path.dirname(csv_file), 'mappings.csv')
            if os.path.exists(mappings_csv):
                column_mappings = self._load_schema_mappings(mappings_csv, column_mappings)
            else:
                print("Warning: File mappings.csv non trovato, skip mappings Schema.org")
            
            # Carica CSV (la prima riga contiene categorie, la seconda le vere intestazioni)
            print("Caricando dati CSV...")
            df = pd.read_csv(csv_file, encoding='utf-8', header=1)  # Usa la seconda riga come header
            print(f"Caricate {len(df)} righe, {len(df.columns)} colonne")
            
            # Crea grafo RDF
            graph = Graph()
            
            # Namespace
            graph.bind("ex", EX)
            graph.bind("schema", SCHEMA)
            graph.bind("wdt", WDT)
            graph.bind("wd", WD)
            graph.bind("rdf", RDF)
            graph.bind("rdfs", RDFS)
            
            # Contatori
            total_triples = 0
            total_vehicles = 0
            dynamic_cache_hits = 0
            api_new_entities = 0
            technical_values = 0
            custom_iris = 0
            literals_kept = 0
            
            print("Generando triple RDF...")
            
            # Processa ogni riga (veicolo)
            for idx, row in df.iterrows():
                # Skip righe vuote
                if pd.isna(row.get('N. inventario')) or str(row.get('N. inventario')).strip() == '':
                    continue
                
                total_vehicles += 1
                inventory_num = str(row['N. inventario']).strip()
                
                # Crea subject per questo veicolo
                subject = self._create_subject_iri(inventory_num)
                
                # Aggiungi tipo: questo è un veicolo
                graph.add((subject, RDF.type, SCHEMA.Vehicle))
                total_triples += 1
                
                # Processa ogni colonna
                for col_name, value in row.items():
                    # Skip colonne senza mapping o valori vuoti
                    if col_name not in column_mappings:
                        continue
                    
                    if pd.isna(value) or str(value).strip() == '' or str(value).strip() == 'nan':
                        continue
                    
                    value_str = str(value).strip()
                    mapping = column_mappings[col_name]
                    predicate_uri = mapping['predicate']
                    schema_predicates = mapping.get('schema_predicates', [])
                    
                    # SPECIAL CASE: Acquisizione con "Dono" -> usa predicato DONOR
                    if col_name == 'Acquisizione' and museum_mappings.is_donation(value_str):
                        donor_predicates = museum_mappings.get_donor_predicates()
                        predicate_uri = donor_predicates['wikidata']
                        schema_predicates = [donor_predicates['schema']]
                    
                    # SPECIAL CASE: Aggiungi productionDate per "Anni di produzione"
                    if col_name == 'Anni di produzione':
                        if 'https://schema.org/productionDate' not in schema_predicates:
                            schema_predicates.append('https://schema.org/productionDate')
                    
                    # Arricchisci il valore (usa predicato Wikidata per decidere)
                    enrichment = self.enrich_single_value(value_str, predicate_uri)
                    
                    if enrichment['action'] == 'keep_original':
                        # Mantieni come literal - genera triple con tutti i predicati
                        graph.add((subject, URIRef(predicate_uri), Literal(value_str, datatype=XSD.string)))
                        total_triples += 1
                        literals_kept += 1
                        
                        # Aggiungi anche predicati Schema.org per interoperabilità
                        for schema_pred in schema_predicates:
                            graph.add((subject, URIRef(schema_pred), Literal(value_str, datatype=XSD.string)))
                            total_triples += 1
                    
                    elif enrichment['action'] == 'create_multiple_entities':
                        # Multiple entità (persone, piloti, etc.)
                        for entity_data in enrichment['entities']:
                            # Triple con predicato Wikidata
                            graph.add((subject, URIRef(predicate_uri), entity_data['iri']))
                            graph.add((entity_data['iri'], RDF.type, entity_data['rdf_type']))
                            graph.add((entity_data['iri'], RDFS.label, Literal(entity_data['original_value'], datatype=XSD.string)))
                            total_triples += 3
                            
                            # Aggiungi anche predicati Schema.org
                            for schema_pred in schema_predicates:
                                graph.add((subject, URIRef(schema_pred), entity_data['iri']))
                                total_triples += 1
                            
                            # Conteggi
                            if entity_data['action'] == 'create_wikidata_iri':
                                if entity_data['source'] == 'dynamic_cache':
                                    dynamic_cache_hits += 1
                                else:
                                    api_new_entities += 1
                    
                    else:
                        # Singola entità o IRI
                        # Triple con predicato Wikidata
                        graph.add((subject, URIRef(predicate_uri), enrichment['iri']))
                        graph.add((enrichment['iri'], RDF.type, enrichment['rdf_type']))
                        graph.add((enrichment['iri'], RDFS.label, Literal(enrichment['original_value'], datatype=XSD.string)))
                        total_triples += 3
                        
                        # Aggiungi anche predicati Schema.org per interoperabilità
                        for schema_pred in schema_predicates:
                            graph.add((subject, URIRef(schema_pred), enrichment['iri']))
                            total_triples += 1
                        
                        # Conteggi per tipo
                        if enrichment['action'] == 'create_technical_iri':
                            technical_values += 1
                        elif enrichment['action'] == 'create_wikidata_iri':
                            if enrichment['source'] == 'dynamic_cache':
                                dynamic_cache_hits += 1
                            else:
                                api_new_entities += 1
                        elif enrichment['action'] == 'create_custom_iri':
                            custom_iris += 1
                
                if (idx + 1) % 10 == 0:
                    print(f"  Processati {idx + 1}/{len(df)} veicoli...")
            
            # Salva grafo
            print("Salvando grafo RDF...")
            output_dir = os.path.dirname(output_file)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            graph.serialize(destination=output_file, format='nt', encoding='utf-8')
            
            # Risultati
            print(f"\n=== RISULTATI GENERAZIONE RDF ===\n")
            print(f"Veicoli processati: {total_vehicles}")
            print(f"Triple generate: {total_triples}")
            print(f"\nDettaglio arricchimento:")
            print(f"  - Literal mantenuti: {literals_kept}")
            print(f"  - Entità Wikidata (da cache): {dynamic_cache_hits}")
            print(f"  - Entità Wikidata (nuove da API): {api_new_entities}")
            print(f"  - Valori tecnici normalizzati: {technical_values}")
            print(f"  - IRI personalizzati: {custom_iris}")
            print(f"\nFile salvato: {output_file}")
            print(f"Cache entità espanso: {len(self.entity_cache)} entità totali")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            print(f"Errore durante elaborazione: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Funzione principale per uso autonomo - generazione RDF da CSV."""
    # Chiedi se cancellare le cache
    clear_cache = input("Vuoi cancellare le cache prima di iniziare? (s/n): ").strip().lower()
    
    if clear_cache in ['s', 'si', 'sì', 'y', 'yes']:
        cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cache")
        cache_files = glob.glob(os.path.join(cache_dir, "*"))
        
        if cache_files:
            print(f"\nEliminazione di {len(cache_files)} file dalla cache...")
            for cache_file in cache_files:
                try:
                    if os.path.isfile(cache_file):
                        os.remove(cache_file)
                        print(f"  ✓ Eliminato: {os.path.basename(cache_file)}")
                except Exception as e:
                    print(f"  ✗ Errore nell'eliminare {os.path.basename(cache_file)}: {e}")
            print("Cache pulita!\n")
        else:
            print("Nessun file di cache da eliminare.\n")
    else:
        print("Cache mantenuta.\n")
    
    enricher = AdvancedSemanticEnricher(use_wikidata_api=True, cache_file="production_cache.pkl")
    
    # File di input e output
    csv_file = "data/museo.csv"
    mapping_file = "data/museum_column_mapping.csv"
    output_file = "output/output_automatic_enriched.nt"
    
    success = enricher.process_csv_to_rdf(csv_file, mapping_file, output_file)
    
    if success:
        print("\nGenerazione RDF completata con successo!")
        print(f"Cache entità finale: {len(enricher.entity_cache)} entità risolte")
    else:
        print("\nErrore nella generazione RDF!")

if __name__ == "__main__":
    main()