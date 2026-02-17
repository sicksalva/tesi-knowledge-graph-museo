#!/usr/bin/env python3
"""
VERSIONE MODIFICATA: Sistema integrato per generazione RDF con TUTTI I LITERALS COME IRI

Questo sistema legge direttamente da museo.csv e genera un grafo RDF trasformando:
1. TUTTI gli attributi in IRI (eccetto la descrizione - campo TESTO)
2. Utilizza format: example.org/{attribute_name}_{normalized_value}
3. Ogni attributo diventa un nodo soggetto con potenziali outgoing edges

Questo crea un grafo completamente connesso con nodi per ogni attributo.
"""

import sys
import os
import csv
import json
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

class AdvancedSemanticEnricherV2:
    """
    Sistema di arricchimento semantico V2: combinazione di entity linking e IRI generici.
    - Entity linking per brand, paese, entità concettuali
    - IRI generici per attributi tecnici
    """
    
    def __init__(self, use_wikidata_api=True, cache_file="advanced_enricher_cache.pkl", convert_to_iris=True):
        """
        use_wikidata_api=True: abilita entity linking per brand, paese, ecc.
        convert_to_iris=True: abilita conversione a IRI generici per altri attributi
        """
        self.convert_to_iris = convert_to_iris
        self.wikidata_linker = WikidataEntityLinker(cache_file=cache_file) if use_wikidata_api else None
        self.use_wikidata_api = use_wikidata_api
        
        # Cache dinamico entità risolte (si espande automaticamente)
        self.entity_cache_file = cache_file.replace('.pkl', '_entities.json') if cache_file else 'entity_cache.json'
        self.entity_cache = self._load_entity_cache()
        
        print(f"Cache entità caricato: {len(self.entity_cache)} entità precedentemente risolte")
        print(f"Wikidata API: {'Attiva' if self.use_wikidata_api else 'Disattivata'}")
        if self.convert_to_iris:
            print("MODALITA' ATTIVA: Entity Linking + Conversione IRI Generici")
        else:
            print("MODALITA': Mantenimento dei literal originali")
    
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
    
    def _save_to_entity_cache(self, value: str, qid: str, entity_type: str, confidence: float, label: str = None):
        """Salva risultato in cache dinamico (si espande automaticamente)."""
        import json
        normalized = value.strip().lower()
        
        self.entity_cache[normalized] = {
            'qid': qid,
            'type': entity_type,
            'confidence': confidence,
            'original_value': value,
            'label': label if label else value
        }
        
        # Salva su disco immediatamente
        try:
            cache_dir = os.path.dirname(self.entity_cache_file)
            if cache_dir and not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)
                
            with open(self.entity_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.entity_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Warning: Impossibile salvare cache entità: {e}")
    
    def _process_single_entity(self, value: str, predicate_str: str):
        """
        Processa singola entità con entity linking Wikidata.
        """
        # Prima controlla cache dinamico
        cached_result = self._check_entity_cache(value)
        if cached_result:
            return {
                'action': 'create_wikidata_iri',
                'original_value': value,
                'wikidata_label': cached_result.get('label', value),
                'iri': WD[cached_result['qid']],
                'rdf_type': WD[cached_result['type']],
                'source': 'dynamic_cache',
                'confidence': cached_result.get('confidence', 1.0)
            }
        
        # Se non in cache, usa API Wikidata
        if self.wikidata_linker:
            # Determina tipo suggerito dai mappings
            suggested_type = museum_mappings.get_entity_type_for_predicate(predicate_str)
            
            # Chiama API
            api_result = self.wikidata_linker.find_best_entity(value, min_confidence=0.6, predicate_context=predicate_str)
            if api_result:
                # Seleziona il tipo più appropriato
                instance_of_types = api_result.get('instance_of', [])
                best_type = museum_mappings.select_best_type_from_instance_of(
                    instance_of_types, 
                    predicate_hint=suggested_type
                )
                
                # Salva in cache dinamico
                wikidata_label = api_result.get('label', value)
                self._save_to_entity_cache(value, api_result['qid'], best_type, api_result['confidence'], wikidata_label)
                
                return {
                    'action': 'create_wikidata_iri',
                    'original_value': value,
                    'wikidata_label': wikidata_label,
                    'iri': WD[api_result['qid']],
                    'rdf_type': WD[best_type],
                    'source': 'wikidata_api_new',
                    'confidence': api_result['confidence']
                }
        
        return None
    
    def split_entities(self, value: str):
        """Divide valori con più entità (persone, designer, etc.) separati da connettori."""
        import re
        parts = re.split(r'\s*(?:,| e | & |;|/|\bper\b|\n)\s*', value)
        entities = []
        for p in parts:
            p = p.strip()
            if (p and len(p) > 3 and 
                not re.match(r'^(di|da|per|con|in|su|a|il|la|le|lo|gli|un|una|dei|delle|dello|della)$', p.lower()) and
                not re.match(r'^[A-Z]+$', p)):
                entities.append(p)
        return entities
    
    def _literal_to_iri(self, value: str, col_name: str) -> URIRef:
        """
        Converte un literal in IRI usando format: example.org/{attribute_name}_{normalized_value}
        
        Ogni attributo diventa un nodo che può essere soggetto di ulteriori relazioni.
        """
        # Normalizza il valore per IRI (mantieni underscore e numeri)
        normalized_value = re.sub(r'[^a-zA-Z0-9\s]', '', value.strip())
        normalized_value = re.sub(r'\s+', '_', normalized_value).lower()
        
        # Se il valore normalizzato è vuoto, usa il primo carattere del valore originale
        if not normalized_value or normalized_value == '_':
            normalized_value = re.sub(r'[^a-zA-Z0-9]', '', value[:10].strip())[:5]
            if not normalized_value:
                normalized_value = "value"
        
        # Normalizza il nome dell'attributo per IRI
        attr_name = re.sub(r'[^a-zA-Z0-9]', '_', col_name.strip()).lower()
        
        # Crea l'IRI
        iri_path = f"{attr_name}_{normalized_value}"
        return EX[iri_path]
    
    def _parse_production_years(self, value: str):
        """
        Analizza gli anni di produzione e determina se sono singoli o range.
        
        Returns:
            dict con 'type': 'single' o 'range', 'start': anno, 'end': anno (se range)
        """
        import re
        # Cerca pattern con separatori: -, /, ,, spazio
        matches = re.findall(r'\d{4}', value)
        
        if len(matches) == 1:
            return {'type': 'single', 'year': matches[0]}
        elif len(matches) >= 2:
            return {'type': 'range', 'start': matches[0], 'end': matches[1]}
        else:
            return {'type': 'unknown', 'value': value}
    
    def _get_acquisition_type(self, value: str):
        """
        Determina il tipo di acquisizione.
        
        Returns:
            'donor' se inizia con DONO, 'acquiredFrom' se inizia con ACQUISTATA, None altrimenti
        """
        value_upper = value.strip().upper()
        if value_upper.startswith('DONO'):
            return 'donor'
        elif value_upper.startswith('ACQUIST'):
            return 'acquiredFrom'
        else:
            return None
    
    def _load_column_mappings(self, mapping_file: str) -> Dict[str, Dict]:
        """Carica mappings colonne CSV -> proprietà RDF (Wikidata + Schema.org)."""
        mappings = {}
        try:
            df = pd.read_csv(mapping_file, encoding='utf-8')
            for _, row in df.iterrows():
                col_name = row['column_name']
                wd_prop = row['wikidata_property']
                schema_prop = row.get('schema_org_property', '')
                
                # Determina URI completo del predicato Wikidata
                if '|' in wd_prop:
                    # Proprietà condizionale (es: P2754|P571|P576)
                    predicate_uri = None  # Sarà determinato runtime
                elif wd_prop.startswith('P') and len(wd_prop) <= 6:
                    # Proprietà Wikidata
                    predicate_uri = f"http://www.wikidata.org/prop/direct/{wd_prop}"
                elif wd_prop.startswith('custom:'):
                    # Proprietà custom
                    custom_name = wd_prop.replace('custom:', '')
                    predicate_uri = f"http://example.org/{custom_name}"
                else:
                    predicate_uri = wd_prop
                
                # Processa predicati Schema.org
                schema_predicates = []
                if schema_prop and not pd.isna(schema_prop):
                    schema_props_list = schema_prop.split('|') if '|' in schema_prop else [schema_prop]
                    for sp in schema_props_list:
                        sp = sp.strip()
                        if sp.startswith('custom:'):
                            schema_predicates.append(f"http://example.org/{sp.replace('custom:', '')}")
                        elif sp and sp != '':
                            schema_predicates.append(f"https://schema.org/{sp}")
                
                mappings[col_name] = {
                    'predicate': predicate_uri,
                    'property_id': wd_prop,
                    'label': row['property_label'],
                    'category': row['macro_category'],
                    'schema_predicates': schema_predicates,
                    'schema_property_raw': schema_prop  # Salva valore raw per logica condizionale
                }
            
            print(f"Caricati {len(mappings)} mappings colonne")
            return mappings
        except Exception as e:
            print(f"Errore caricamento mappings: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _load_schema_mappings(self, mappings_file: str, column_mappings: Dict) -> Dict[str, Dict]:
        """Carica mappings aggiuntivi da mappings.csv (Schema.org, etc.)."""
        try:
            df = pd.read_csv(mappings_file, encoding='utf-8')
            schema_count = 0
            
            for _, row in df.iterrows():
                source = row.get('Source', '')
                if pd.isna(source) or source == '':
                    continue
                
                if '/data/' in source:
                    col_name_encoded = source.split('/data/')[-1]
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
                        schema_props = []
                        
                        schema_org = row.get('Schema.org', '')
                        if not pd.isna(schema_org) and schema_org.strip() != '':
                            schema_props.append(schema_org.strip())
                        
                        for i in [1, 2, 3, 4]:
                            opt = row.get(f'Option {i}', '')
                            if not pd.isna(opt) and opt.strip() != '':
                                schema_props.append(opt.strip())
                        
                        for schema_prop in schema_props:
                            if self._is_valid_predicate(schema_prop):
                                if 'purl.org' in schema_prop or '/dc/terms' in schema_prop:
                                    continue
                                
                                if schema_prop.startswith('http://schema.org/'):
                                    schema_uri = schema_prop.replace('http://', 'https://')
                                elif schema_prop.startswith('https://schema.org/'):
                                    schema_uri = schema_prop
                                elif schema_prop.startswith('http'):
                                    schema_uri = schema_prop
                                else:
                                    schema_uri = f"https://schema.org/{schema_prop}"
                                
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
        
        if ',' in value:
            return False
        
        if re.match(r'^\d+\s', value):
            return False
        
        if value.count(' ') > 2:
            return False
        
        if value.startswith('http://') or value.startswith('https://'):
            return True
        
        if re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', value):
            return True
        
        return False
    
    def _create_subject_iri(self, inventory_number: str) -> URIRef:
        """Crea IRI per subject (veicolo) basato su numero inventario."""
        normalized = re.sub(r'[^a-zA-Z0-9]', '_', inventory_number.strip())
        return EX[f"vehicle_{normalized}"]
    
    def process_csv_to_rdf(self, csv_file: str, mapping_file: str, output_file: str) -> bool:
        """
        Processa CSV museo generando RDF con TUTTI I LITERALS TRASFORMATI IN IRI (v2).
        
        Versione modificata: ogni attributo (eccetto la descrizione) diventa un IRI
        che può essere soggetto di ulteriori relazioni.
        """
        
        print("\n" + "=" * 80)
        print("=== GENERAZIONE RDF - VERSIONE V2 (TUTTI I LITERALS COME IRI) ===")
        print("=" * 80)
        print(f"Input CSV: {csv_file}")
        print(f"Mappings: {mapping_file}")
        print(f"Output: {output_file}")
        print(f"Modalità: {'Conversione a IRI' if self.convert_to_iris else 'Literal originali'}")
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
            
            # NOTA: mappings.csv è obsoleto e contiene mappings Schema.org errati.
            # Usiamo SOLO museum_column_mapping.csv che è curato e corretto.
            print("INFO: Uso SOLO museum_column_mapping.csv (mappings.csv obsoleto ignorato)")
            
            # Carica CSV
            print("Caricando dati CSV...")
            df = pd.read_csv(csv_file, encoding='utf-8', header=1)
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
            literals_converted_to_iris = 0
            descriptions_kept_as_literal = 0
            
            print("\nGenerando triple RDF...")
            
            # Processa ogni riga (veicolo)
            for idx, row in df.iterrows():
                # Skip righe vuote
                if pd.isna(row.get('N. inventario')) or str(row.get('N. inventario')).strip() == '':
                    continue
                
                total_vehicles += 1
                inventory_num = str(row['N. inventario']).strip()
                
                # Crea subject per questo veicolo
                subject = self._create_subject_iri(inventory_num)
                
                # Aggiungi tipo
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
                    property_id = mapping.get('property_id', '')
                    
                    # Se predicate_uri è None (proprietà condizionale), gestiamo nei casi speciali
                    if predicate_uri is None and col_name not in ['Anni di produzione', 'Acquisizione']:
                        # Skip se non abbiamo handler speciale
                        continue
                    
                    # ========================================================================
                    # LOGICHE CONDIZIONALI SPECIALI
                    # ========================================================================
                    
                    # CASO SPECIALE 1: Anni di produzione (single year vs range)
                    if col_name == 'Anni di produzione':
                        years_info = self._parse_production_years(value_str)
                        
                        if years_info['type'] == 'single':
                            # Un solo anno: usa productionDate + P2754
                            year_iri = self._literal_to_iri(value_str, col_name)
                            graph.add((subject, WDT['P2754'], year_iri))
                            graph.add((subject, SCHEMA.productionDate, year_iri))
                            graph.add((year_iri, RDFS.label, Literal(value_str, datatype=XSD.string)))
                            graph.add((year_iri, RDF.type, EX['Attribute']))
                            total_triples += 4
                            literals_converted_to_iris += 1
                            continue
                            
                        elif years_info['type'] == 'range':
                            # Range di anni: SOLO schema:startDate/endDate con IRI, NO P2754
                            # Crea IRI per anno inizio
                            start_iri = self._literal_to_iri(years_info['start'], 'anno')
                            graph.add((start_iri, RDFS.label, Literal(years_info['start'], datatype=XSD.string)))
                            graph.add((start_iri, RDF.type, EX['Year']))
                            
                            # Crea IRI per anno fine
                            end_iri = self._literal_to_iri(years_info['end'], 'anno')
                            graph.add((end_iri, RDFS.label, Literal(years_info['end'], datatype=XSD.string)))
                            graph.add((end_iri, RDF.type, EX['Year']))
                            
                            # Collega con P571/P576 e schema:startDate/endDate
                            graph.add((subject, WDT['P571'], start_iri))
                            graph.add((subject, WDT['P576'], end_iri))
                            graph.add((subject, SCHEMA.startDate, start_iri))
                            graph.add((subject, SCHEMA.endDate, end_iri))
                            
                            total_triples += 8
                            literals_converted_to_iris += 2
                            continue
                    
                    # CASO SPECIALE 2: Acquisizione (DONO vs ACQUISTATA)
                    if col_name == 'Acquisizione':
                        acquisition_type = self._get_acquisition_type(value_str)
                        acquisition_iri = self._literal_to_iri(value_str, col_name)
                        
                        # Predicato Wikidata custom
                        graph.add((subject, EX['acquisitionMethod'], acquisition_iri))
                        graph.add((acquisition_iri, RDFS.label, Literal(value_str, datatype=XSD.string)))
                        graph.add((acquisition_iri, RDF.type, EX['Attribute']))
                        total_triples += 3
                        
                        # Predicato Schema.org condizionale
                        if acquisition_type == 'donor':
                            graph.add((subject, SCHEMA.donor, acquisition_iri))
                            total_triples += 1
                        elif acquisition_type == 'acquiredFrom':
                            graph.add((subject, SCHEMA.acquiredFrom, acquisition_iri))
                            total_triples += 1
                        
                        literals_converted_to_iris += 1
                        continue
                    
                    # ========================================================================
                    # **VERSIONE V2: REGOLE BASATE SU MUSEUM_MAPPINGS (3 TIER)**
                    # ========================================================================
                    
                    # 1. Se il predicato deve rimanere ALWAYS literal (descrizione + museo specifici)
                    if museum_mappings.should_keep_literal(predicate_uri):
                        # Mantieni come literal
                        graph.add((subject, URIRef(predicate_uri), Literal(value_str, datatype=XSD.string)))
                        total_triples += 1
                        descriptions_kept_as_literal += 1
                        
                        # Aggiungi anche predicati Schema.org
                        for schema_pred in schema_predicates:
                            graph.add((subject, URIRef(schema_pred), Literal(value_str, datatype=XSD.string)))
                            total_triples += 1
                    
                    # 2. Se il predicato richiede ENTITY LINKING (brand, country, designer, model)
                    elif museum_mappings.should_use_entity_linking(predicate_uri):
                        # CASO SPECIALE: Modello → aggiungi contesto Marca per ricerca Wikidata
                        search_value = value_str
                        if col_name == 'Modello' and 'Marca' in row:
                            brand = str(row['Marca']).strip()
                            if brand and not pd.isna(row['Marca']) and brand.lower() != 'nan':
                                search_value = f"{brand} {value_str}"  # "Ferrari 308 GTB"
                                print(f"  → Ricerca modello con contesto: '{search_value}'")
                        
                        # Gestisci possibili entità multiple (es. "Volkswagen, Porsche")
                        entities = self.split_entities(search_value)
                        
                        for entity_value in entities:
                            # Prova entity linking con API Wikidata
                            result = self._process_single_entity(entity_value, predicate_uri)
                            
                            if result and result['action'] == 'create_wikidata_iri':
                                # Usa IRI Wikidata
                                wikidata_iri = result['iri']
                                wikidata_label = result['wikidata_label']
                                rdf_type = result['rdf_type']
                                
                                # Triple principale
                                graph.add((subject, URIRef(predicate_uri), wikidata_iri))
                                
                                # Aggiungi tipo e label per l'entità Wikidata
                                graph.add((wikidata_iri, RDF.type, rdf_type))
                                graph.add((wikidata_iri, RDFS.label, Literal(wikidata_label, datatype=XSD.string)))
                                
                                total_triples += 3
                                literals_converted_to_iris += 1
                                
                                # Aggiungi anche con predicati Schema.org
                                for schema_pred in schema_predicates:
                                    graph.add((subject, URIRef(schema_pred), wikidata_iri))
                                    total_triples += 1
                            else:
                                # Fallback: crea IRI generica se entity linking fallisce
                                attribute_iri = self._literal_to_iri(entity_value, col_name)
                                graph.add((subject, URIRef(predicate_uri), attribute_iri))
                                graph.add((attribute_iri, RDFS.label, Literal(entity_value, datatype=XSD.string)))
                                graph.add((attribute_iri, RDF.type, EX['Attribute']))
                                total_triples += 3
                                literals_converted_to_iris += 1
                    
                    # 3. Se il predicato ha valori literal che devono diventare IRI GENERICA
                    elif museum_mappings.should_convert_literal_to_iri(predicate_uri):
                        # Converti il valore literal in IRI generica (example.org)
                        attribute_iri = self._literal_to_iri(value_str, col_name)
                        
                        # Triple: subject -> predicate -> attribute_iri
                        graph.add((subject, URIRef(predicate_uri), attribute_iri))
                        
                        # Aggiungi il valore originale come label del nodo attributo
                        graph.add((attribute_iri, RDFS.label, Literal(value_str, datatype=XSD.string)))
                        graph.add((attribute_iri, RDF.type, EX['Attribute']))
                        
                        total_triples += 3
                        literals_converted_to_iris += 1
                        
                        # Aggiungi anche con predicati Schema.org per interoperabilità
                        for schema_pred in schema_predicates:
                            graph.add((subject, URIRef(schema_pred), attribute_iri))
                            total_triples += 1
                    
                    else:
                        # 4. Per tutti gli altri: mantieni come literal (comportamento di default)
                        graph.add((subject, URIRef(predicate_uri), Literal(value_str, datatype=XSD.string)))
                        total_triples += 1
                        
                        # Aggiungi anche predicati Schema.org
                        for schema_pred in schema_predicates:
                            graph.add((subject, URIRef(schema_pred), Literal(value_str, datatype=XSD.string)))
                            total_triples += 1
                
                if (idx + 1) % 10 == 0:
                    print(f"  Processati {idx + 1}/{len(df)} veicoli...")
            
            # Salva grafo
            print("\nSalvando grafo RDF...")
            output_dir = os.path.dirname(output_file)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            graph.serialize(destination=output_file, format='nt', encoding='utf-8')
            
            # Risultati
            print(f"\n" + "=" * 80)
            print(f"=== RISULTATI GENERAZIONE RDF V2 ===")
            print("=" * 80)
            print(f"\nVeicoli processati: {total_vehicles}")
            print(f"Triple generate: {total_triples}")
            print(f"\nConversione Attributes:")
            print(f"  - Literals convertiti in IRI: {literals_converted_to_iris}")
            print(f"  - Descrizioni mantenute come literal: {descriptions_kept_as_literal}")
            print(f"\nFile salvato: {output_file}")
            print("=" * 80 + "\n")
            
            return True
            
        except Exception as e:
            print(f"Errore durante elaborazione: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Funzione principale - esegui versione V2 con entity linking + generic IRIs"""
    print("\n=== GENERAZIONE RDF VERSIONE 2 ===")
    print("Configurazione Dichiarativa: Literals → IRI Basato su museum_mappings.py\n")
    
    # Crea l'enricher V2 con Wikidata API attivata per entity linking
    enricher = AdvancedSemanticEnricherV2(
        use_wikidata_api=True,  # ATTIVATO: usa Wikidata API per brand/country/designer
        cache_file="caches/production_cache_v2.pkl",
        convert_to_iris=True  # ATTIVA: converti tutto in IRI
    )
    
    # File di input e output
    csv_file = "data/museo.csv"
    mapping_file = "data/museum_column_mapping.csv"
    output_file = "output/output_automatic_enriched_v2.nt"
    
    success = enricher.process_csv_to_rdf(csv_file, mapping_file, output_file)
    
    if success:
        print("\nGenerazione RDF V2 completata con successo!")
        print(f"Output salvato in: {output_file}")
    else:
        print("\nErrore nella generazione RDF!")

if __name__ == "__main__":
    main()
