# Mappature personalizzate per dataset Museo Automobile
# Formato: predicato_originale -> predicato_wikidata_target

# Mappature personalizzate per dataset Museo Automobile
# Integrato con mappings.csv - Formato: predicato_originale -> predicato_target
# Seguendo la tabella decisionale: solo entità concettuali diventano IRI

museum_mappings = {
    # VETTURA - Solo entità che devono diventare IRI
    "http://example.org/N_inventario": "http://www.wikidata.org/prop/direct/P528",  # catalogue code (LITERAL)
    "http://example.org/Marca": "http://www.wikidata.org/prop/direct/P1716",      # brand (IRI)
    "http://example.org/Paese": "http://www.wikidata.org/prop/direct/P495",       # country of origin (IRI) 
    
    # ACQUISIZIONE (tutte LITERAL secondo tabella)
    "http://example.org/Acquisizione": "http://schema.org/purchaseDate",          # purchase date (LITERAL)
    "http://example.org/Anno": "http://www.wikidata.org/prop/direct/P5444",      # model year (LITERAL)
    "http://example.org/Anni_di_produzione": "http://www.wikidata.org/prop/direct/P2754", # production date (LITERAL)
    
    # SPECIFICHE TECNICHE (tutte LITERAL secondo tabella) 
    "http://example.org/Cilindrata": "http://schema.org/engineDisplacement",     # engine displacement (LITERAL)
    "http://example.org/Potenza": "http://schema.org/EnginePower",               # engine power (LITERAL)
    "http://example.org/Velocità": "http://schema.org/speed",                    # speed (LITERAL)
    "http://example.org/Autonomia": "http://www.wikidata.org/prop/direct/P2073", # vehicle range (LITERAL)
    "http://example.org/Consumo": "http://schema.org/fuelConsumption",          # fuel consumption (LITERAL)
    "http://example.org/Cambio": "http://schema.org/numberOfForwardGears",      # number of gears (LITERAL)
    "http://example.org/Batterie": "http://www.wikidata.org/prop/direct/P4140", # energy storage capacity (LITERAL)
    "http://example.org/Telaio": "http://www.wikidata.org/prop/direct/P7045",   # chassis (LITERAL)
    "http://example.org/Motore": "http://www.wikidata.org/prop/direct/P1002",   # engine configuration (LITERAL)
    "http://example.org/Trasmissione": "http://schema.org/AllWheelDriveConfiguration", # transmission (LITERAL)
    "http://example.org/Modello": "http://schema.org/model",                     # model name (LITERAL)
    
    # ENTITÀ CONCETTUALI (IRI secondo tabella)
    "http://example.org/Alimentazione": "http://www.wikidata.org/prop/direct/P516", # powered by (IRI)
    "http://example.org/Tipo_di_motore": "http://schema.org/engineType",        # engine type (IRI)
    "http://example.org/Carrozzeria": "http://schema.org/bodyType",             # body type (IRI)
    
    # STORIA E PERSONE (IRI)
    "http://example.org/Carrozzeria_Designer": "http://www.wikidata.org/prop/direct/P287", # designed by (IRI per persone)
    "http://example.org/Piloti": "http://example.org/racing/drivers",           # racing drivers (IRI per persone)
    "http://example.org/Corse": "http://www.wikidata.org/prop/direct/P166",     # award received (IRI)
    
    # MUSEO SPECIFICI (LITERAL)
    "http://example.org/Piano": "http://example.org/museum/floorLevel",         # floor level (LITERAL)
    "http://example.org/Sezione": "http://example.org/museum/section",          # museum section (LITERAL)
    "http://example.org/TESTO": "http://www.w3.org/2000/01/rdf-schema#comment", # description -> comment (LITERAL)
}

# Proprietà che DEVONO rimanere literal (seguendo tabella decisionale + mappings.csv)
literal_only_properties = [
    # Museo specifici
    "http://example.org/floorLevel",
    "http://example.org/museumSection", 
    "http://example.org/N_inventario",
    "http://www.wikidata.org/prop/direct/P217",   # inventory number
    "http://www.wikidata.org/prop/direct/P528",   # catalogue code
    
    # ANNI e DATE (PRIORITÀ ASSOLUTA - mai IRI)
    "http://example.org/Anno",
    "http://example.org/Anni_di_produzione", 
    "http://example.org/Anno_acquisizione",
    "http://example.org/Anno_carrozzeria",
    "http://schema.org/purchaseDate",             # purchase date
    "http://schema.org/dateVehicleFirstRegistered", # vehicle registration date
    "http://schema.org/modelDate",                # model date
    "http://www.wikidata.org/prop/direct/P571",   # inception
    "http://www.wikidata.org/prop/direct/P2754",  # production date
    "http://www.wikidata.org/prop/direct/P580",   # start time
    "http://www.wikidata.org/prop/direct/P585",   # point in time
    "http://www.wikidata.org/prop/direct/P5444",  # model year
    
    # MODELLO (sempre literal)
    "http://example.org/Modello",
    "http://schema.org/model",                    # model name
    "https://schema.org/model",                   # model name (HTTPS)
    "http://www.wikidata.org/prop/direct/P1559", # name in native language
    
    # DATI NUMERICI TECNICI (seguendo tabella + mappings.csv)
    "http://example.org/Potenza",
    "http://schema.org/EnginePower",             # engine power
    "https://schema.org/EnginePower",            # engine power (HTTPS)
    "http://www.wikidata.org/prop/direct/P2109", # nominal power output
    "http://example.org/Cilindrata", 
    "http://schema.org/engineDisplacement",     # engine displacement
    "https://schema.org/engineDisplacement",    # engine displacement (HTTPS)
    "http://www.wikidata.org/prop/direct/P8628", # engine displacement
    "http://example.org/Velocità",
    "http://example.org/Velocit_",               # velocità with underscore encoding
    "http://schema.org/speed",                   # speed
    "https://schema.org/speed",                  # speed (HTTPS)
    "http://www.wikidata.org/prop/direct/P2052", # speed
    "http://example.org/Autonomia",
    "http://schema.org/fuelEfficiency",         # fuel efficiency
    "https://schema.org/fuelEfficiency",        # fuel efficiency (HTTPS)
    "http://www.wikidata.org/prop/direct/P2073", # vehicle range
    "http://example.org/Consumo",
    "http://schema.org/fuelConsumption",        # fuel consumption
    "https://schema.org/fuelConsumption",       # fuel consumption (HTTPS)
    "http://example.org/Cambio",
    "http://schema.org/numberOfForwardGears",   # number of gears
    "https://schema.org/numberOfForwardGears",  # number of gears (HTTPS)
    "http://example.org/Motore",
    "http://www.wikidata.org/prop/direct/P1002", # engine configuration
    "http://example.org/Trasmissione",
    "http://schema.org/AllWheelDriveConfiguration", # transmission config
    "https://schema.org/AllWheelDriveConfiguration", # transmission config (HTTPS)
    "http://example.org/Trazione",
    "http://schema.org/DriveWheelConfiguration", # drive wheel config
    "https://schema.org/DriveWheelConfiguration", # drive wheel config (HTTPS)
    "http://example.org/Telaio",
    "http://www.wikidata.org/prop/direct/P7045", # chassis
    "http://example.org/Batterie",
    "http://www.wikidata.org/prop/direct/P4140", # energy storage capacity
    
    # Altri custom automotive (da mappings.csv)
    "http://example.org/automotive/transmissionSystem",
    "http://example.org/automotive/driveSystem",
    "http://example.org/automotive/driveType",
    "http://example.org/automotive/range",
    "http://example.org/automotive/fuelConsumption"
]

# Proprietà per entità che DEVONO diventare IRI (solo entità concettuali)
iri_target_properties = [
    # BRAND/MARCA - Entity linking a Wikidata
    "http://example.org/Marca",
    "http://schema.org/brand",                   # brand
    "https://schema.org/brand",                  # brand (HTTPS version)
    "http://www.wikidata.org/prop/direct/P176",  # manufacturer
    "http://www.wikidata.org/prop/direct/P1716", # brand
    
    # PAESE - Entity linking a Wikidata
    "http://example.org/Paese",
    "http://schema.org/countryOfOrigin",         # country of origin
    "http://www.wikidata.org/prop/direct/P495",  # country of origin
    
    # ENTITÀ CONCETTUALI - Alimentazione/fuel type
    "http://example.org/Alimentazione",
    "http://schema.org/fuelType",               # fuel type
    "http://www.wikidata.org/prop/direct/P516", # powered by
    "http://www.wikidata.org/prop/direct/P618", # source of energy
    
    # ENTITÀ CONCETTUALI - Tipo di motore/engine type
    "http://example.org/Tipo_di_motore",
    "http://schema.org/engineType",             # engine type
    "http://schema.org/EngineSpecification",    # engine specification
    
    # ENTITÀ CONCETTUALI - Carrozzeria/body type
    "http://example.org/Carrozzeria",
    "http://schema.org/bodyType",               # body type
    
    # ENTITÀ CONCETTUALI - Designer/Carrozziere (persone)
    "http://example.org/Carrozzeria_Designer",
    "http://schema.org/manufacturer",           # manufacturer/designer 
    "http://www.wikidata.org/prop/direct/P287", # designed by
    
    # ENTITÀ CONCETTUALI - Piloti (persone)
    "http://example.org/Piloti",
    "http://schema.org/Person",                 # person
    "http://example.org/racing/drivers",
    
    # ENTITÀ CONCETTUALI - Competizioni/Corse (eventi)
    "http://example.org/Corse",
    "http://schema.org/award",                  # award
    "http://www.wikidata.org/prop/direct/P166", # award received
    "http://www.wikidata.org/prop/direct/P641"  # sport
]

# Proprietà che usano rdfs:comment per descrizioni lunghe
description_properties = [
    "http://www.w3.org/2000/01/rdf-schema#comment",
    "http://example.org/TESTO",
    "http://schema.org/Description"              # description da mappings.csv
]

# ============================================================================
# LOGICA PER ENTITÀ MULTIPLE (designer, piloti, etc.)
# ============================================================================
multiple_entities_predicates = [
    'http://example.org/Carrozzeria_Designer',
    'http://www.wikidata.org/prop/direct/P287',  # designed by
    'http://example.org/Piloti',
    'http://example.org/racing/drivers',
    'http://schema.org/Person',
    'http://schema.org/manufacturer'  # può contenere più designer/manufacturer
]

# ============================================================================
# PATTERN PER RICONOSCERE ANNI (devono rimanere LITERAL)
# ============================================================================
import re

def is_year_value(value: str) -> bool:
    """Determina se un valore è un anno o range di anni."""
    if not value or not isinstance(value, str):
        return False
    
    value = value.strip()
    year_patterns = [
        r'^\d{4}$',                              # 1990
        r'^\d{4}[-–]\d{4}$',                     # 1990-1995
        r'^(19|20)\d{2}$',                       # 1900-2099
        r'^(19|20)\d{2}[-–](19|20)\d{2}$'        # 1990-1995 con range completo
    ]
    
    for pattern in year_patterns:
        if re.match(pattern, value):
            return True
    return False

# ============================================================================
# TIPI DI ENTITÀ WIKIDATA PER PREDICATI
# ============================================================================
entity_type_mappings = {
    # Persone/People (designer, piloti)
    'http://example.org/Carrozzeria_Designer': 'Q5',  # human/person
    'http://www.wikidata.org/prop/direct/P287': 'Q5',  # designed by
    'http://example.org/Piloti': 'Q5',                 # human/person
    'http://example.org/racing/drivers': 'Q5',         # human/person
    'http://schema.org/Person': 'Q5',                  # human/person
    
    # Competizioni/Awards/Eventi
    'http://example.org/Corse': 'Q18649705',           # competition/event
    'http://schema.org/award': 'Q18649705',            # competition/event
    'http://www.wikidata.org/prop/direct/P166': 'Q18649705',  # award received
    'http://www.wikidata.org/prop/direct/P641': 'Q18649705',  # sport
    
    # Default per entità generiche (alimentazione, tipo motore, carrozzeria, etc.)
    'default': 'Q35120'  # entity (generic)
}

# ============================================================================
# PREFISSI PER IRI PERSONALIZZATI (basati su tipo concettuale)
# ============================================================================
custom_iri_prefixes = {
    'motore': 'engine_type',
    'engine': 'engine_type',
    'carrozzeria': 'body_type',
    'body': 'body_type',
    'alimentazione': 'fuel_type',
    'fuel': 'fuel_type',
    'default': 'concept'
}

# ============================================================================
# LOGICA PER DESCRIZIONI LUNGHE
# ============================================================================
def is_long_description(text: str) -> bool:
    """
    Determina se il testo è una descrizione lunga che dovrebbe usare rdfs:comment.
    """
    if not text or len(text.strip()) < 50:
        return False
        
    # Indicatori di descrizioni lunghe vs labels brevi
    description_indicators = [
        # Presenza di frasi complete (contiene punti)
        r'\.\s+[A-Z]',  # Punto seguito da spazio e maiuscola (nuova frase)
        
        # Testo molto lungo (>200 caratteri)
        lambda t: len(t.strip()) > 200,
        
        # Pattern tipici di descrizioni storiche/narrative
        r'\b(fu|venne|era|divenne|nacque|fondò|produsse|costruì)\b',
        r'\b(nel|dal|al|tra il|durante|epoca|periodo)\s+\d{4}',
        r'\b(storia|fondazione|caratteristiche|descrizione)\b',
        
        # Presenza di più di 3 virgole (elenchi dettagliati)
        lambda t: t.count(',') > 3,
        
        # Pattern narrativi specifici del museo
        r'(al Museo|esposto|vettura|automobile|modello.*fu|prodotta.*tra)'
    ]
    
    # Controlla pattern regex
    for indicator in description_indicators:
        if callable(indicator):
            if indicator(text):
                return True
        else:
            if re.search(indicator, text, re.IGNORECASE):
                return True
    
    return False

def generate_appropriate_label(description: str, predicate_str: str) -> str:
    """
    Genera un label appropriato da una descrizione lunga.
    """
    # Estratti comuni per diversi tipi di predicati
    if 'brand' in predicate_str.lower():
        # Per brand: cerca nomi di aziende
        brands = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b', description[:100])
        if brands:
            return brands[0]
            
    elif 'anno' in predicate_str.lower() or 'year' in predicate_str.lower():
        # Per anni: cerca date a 4 cifre
        years = re.findall(r'\b(1[89]\d{2}|20\d{2})\b', description)
        if years:
            return years[0]
            
    # Fallback: prime 3-4 parole significative
    words = re.findall(r'\b[A-Za-z]+\b', description)
    if words:
        significant_words = [w for w in words[:6] if len(w) > 2][:4]
        return ' '.join(significant_words)
    
    # Ultimo fallback: primi 30 caratteri
    return description[:30].strip() + "..." if len(description) > 30 else description.strip()

def get_custom_iri_prefix(predicate_str: str) -> str:
    """
    Determina il prefisso appropriato per un IRI personalizzato basato sul predicato.
    """
    predicate_lower = predicate_str.lower()
    
    for keyword, prefix in custom_iri_prefixes.items():
        if keyword != 'default' and keyword in predicate_lower:
            return prefix
    
    return custom_iri_prefixes['default']

def get_entity_type_for_predicate(predicate_str: str) -> str:
    """
    Determina il tipo di entità Wikidata appropriato per un predicato.
    """
    return entity_type_mappings.get(predicate_str, entity_type_mappings['default'])

def is_multiple_entities_predicate(predicate_str: str) -> bool:
    """
    Determina se un predicato può contenere multiple entità (persone, designer, etc.).
    """
    return predicate_str in multiple_entities_predicates

def is_donation(value: str) -> bool:
    """
    Determina se un valore di acquisizione è una donazione.
    """
    if not value or not isinstance(value, str):
        return False
    
    value_lower = value.lower()
    donation_keywords = ['dono', 'donazione', 'donato', 'gift', 'donated', 'donation']
    
    return any(keyword in value_lower for keyword in donation_keywords)

def get_donor_predicates():
    """
    Ritorna i predicati per donatore (Wikidata e Schema.org).
    """
    return {
        'wikidata': 'http://www.wikidata.org/prop/direct/P1028',  # donated by
        'schema': 'https://schema.org/sponsor'  # sponsor/donatore
    }