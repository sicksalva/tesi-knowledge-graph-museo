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

# ============================================================================
# GESTIONE DEGLI ATTRIBUTE VALUE
# ============================================================================
# Proprietà che DEVONO RIMANERE LITERAL (descrizione + posizione museo)
literal_only_properties = [
    # Museo specifici - RIMANGONO ALWAYS LITERAL
    "http://example.org/floorLevel",
    "http://example.org/museumSection", 
    "http://example.org/museum/floorLevel",
    "http://example.org/museum/section",
    "http://example.org/N_inventario",
    "http://www.wikidata.org/prop/direct/P217",   # inventory number - LITERAL
    "http://www.wikidata.org/prop/direct/P528",   # catalogue code - LITERAL
    "https://schema.org/identifier",              # identifier - LITERAL
    "http://schema.org/identifier",
    
    # DESCRIZIONE - RIMANE SEMPRE LITERAL
    "http://www.w3.org/2000/01/rdf-schema#comment",
    "http://example.org/TESTO",
    "http://example.org/description",  # custom:description
    "http://schema.org/description",
    "https://schema.org/description",
]

# ============================================================================
# Proprietà i cui VALORI LITERAL devono diventare IRI GENERICI (example.org/...)
# SENZA entity linking (solo normalizzazione)
# ============================================================================
literal_value_to_iri_properties = [
    # WIKIDATA Properties - Valori literal -> IRI generici
    "http://www.wikidata.org/prop/direct/P516",  # powered by (tipo motore)
    "http://www.wikidata.org/prop/direct/P1002", # engine configuration
    "http://www.wikidata.org/prop/direct/P1028", # donated by
    # P1559 (modello) rimosso: ora fa entity linking (vedi iri_target_properties)
    "http://www.wikidata.org/prop/direct/P2052", # speed
    "http://www.wikidata.org/prop/direct/P2109", # nominal power output
    "http://www.wikidata.org/prop/direct/P2754", # production date (solo anno singolo)
    "http://www.wikidata.org/prop/direct/P571",  # inception (anno inizio)
    "http://www.wikidata.org/prop/direct/P576",  # end time (anno fine)
    "http://www.wikidata.org/prop/direct/P580",  # start time (anno acquisizione)
    "http://www.wikidata.org/prop/direct/P585",  # point in time
    "http://www.wikidata.org/prop/direct/P8628", # engine displacement
    
    # CUSTOM Properties - Valori literal -> IRI generici
    "http://example.org/acquisitionMethod",      # acquisition method (ACQUISIZIONE)
    
    # SCHEMA.ORG Properties - Valori literal -> IRI generici
    "https://schema.org/BusOrCoach",
    "http://schema.org/BusOrCoach",
    "https://schema.org/EnginePower",            # engine power
    "http://schema.org/EnginePower",
    "https://schema.org/vehicleEngine",          # vehicle engine (tipo motore)
    "http://schema.org/vehicleEngine",
    "https://schema.org/dateVehicleFirstRegistered",
    "http://schema.org/dateVehicleFirstRegistered",
    "https://schema.org/dataVehicleFirstRegistered", # variante con 'data' invece di 'date'
    "http://schema.org/dataVehicleFirstRegistered",
    "https://schema.org/engineDisplacement",     # engine displacement
    "http://schema.org/engineDisplacement",
    # identifier RIMOSSO: deve rimanere literal (P217)
    "https://schema.org/model",                  # model name
    "http://schema.org/model",
    "https://schema.org/productionDate",         # production date
    "http://schema.org/productionDate",
    "https://schema.org/startDate",              # start date (anno inizio)
    "http://schema.org/startDate",
    "https://schema.org/endDate",                # end date (anno fine)
    "http://schema.org/endDate",
    "https://schema.org/modelDate",              # model date (anno modello)
    "http://schema.org/modelDate",
    "https://schema.org/sponsor",                # sponsor/donor
    "http://schema.org/sponsor",
    "https://schema.org/acrissCode",             # acriss code
    "http://schema.org/acrissCode",
    "https://schema.org/purchaseDate",           # purchase date
    "http://schema.org/purchaseDate",
    "https://schema.org/vehicleModelDate",       # vehicle model date
    "http://schema.org/vehicleModelDate",
    "https://schema.org/vehicleIdentificationNumber",
    "http://schema.org/vehicleIdentificationNumber",
    "https://schema.org/vehicleTransmission",    # transmission
    "http://schema.org/vehicleTransmission",
    "https://schema.org/speed",                  # speed
    "http://schema.org/speed",
]

# Proprietà per entità che DEVONO diventare IRI (solo entità concettuali)
# ============================================================================
# Proprietà per entità che richiedono ENTITY LINKING con Wikidata API.
# I valori literal vengono cercati su Wikidata e trasformati in entità Wikidata
# Es: "Germania" → http://www.wikidata.org/entity/Q183
# ============================================================================
iri_target_properties = [
    # MARCA (manufacturer/brand) - Entity linking a Wikidata
    "http://example.org/Marca",
    "http://schema.org/brand",
    "https://schema.org/brand",
    "http://www.wikidata.org/prop/direct/P176",  # manufacturer
    "http://www.wikidata.org/prop/direct/P1716", # brand
    
    # MODELLO (model name) - Entity linking a Wikidata per modelli specifici
    "http://example.org/Modello",
    "http://schema.org/model",
    "https://schema.org/model",
    "http://www.wikidata.org/prop/direct/P1559", # name in native language
    
    # PAESE (country) - Entity linking a Wikidata
    "http://example.org/Paese",
    "http://schema.org/countryOfOrigin",
    "https://schema.org/countryOfOrigin",
    "http://www.wikidata.org/prop/direct/P495",  # country of origin
    
    # DESIGNER/CARROZZIERE (designers) - Entity linking per persone/aziende
    "http://example.org/Carrozzeria_Designer",
    "http://schema.org/manufacturer",
    "https://schema.org/manufacturer",
    "http://www.wikidata.org/prop/direct/P287", # designed by
    
    # PILOTI (racing drivers) - Entity linking per persone
    "http://example.org/Piloti",
    "http://example.org/racingDrivers",  # custom:racingDrivers
    "http://schema.org/Person",
    "https://schema.org/Person",
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
    'http://example.org/racingDrivers',  # custom:racingDrivers
    'http://schema.org/Person',
    'https://schema.org/Person',
    'http://schema.org/manufacturer',  # può contenere più designer/manufacturer
    'https://schema.org/manufacturer'
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
    
    # Brand/Manufacturer
    'https://schema.org/brand': 'Q786820',             # car manufacturer
    'http://www.wikidata.org/prop/direct/P176': 'Q786820',  # manufacturer
    'http://www.wikidata.org/prop/direct/P1716': 'Q786820',  # brand
    
    # Country/Paese
    'https://schema.org/countryOfOrigin': 'Q6256',     # country
    'http://www.wikidata.org/prop/direct/P495': 'Q6256',    # country of origin
    'http://www.wikidata.org/prop/direct/P17': 'Q6256',     # country
    
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

def select_best_type_from_instance_of(instance_of_list: list, predicate_hint: str = None) -> str:
    """
    Seleziona il tipo più appropriato da una lista di tipi P31 (instance_of).
    
    Args:
        instance_of_list: Lista di QID dai claims P31
        predicate_hint: Tipo suggerito dal predicato (opzionale)
    
    Returns:
        Il QID del tipo più appropriato
    """
    if not instance_of_list:
        return predicate_hint if predicate_hint else 'Q35120'
    
    # Definizione di priorità per categorie di tipi
    priority_types = {
        # Brand/Manufacturer automotive (massima priorità)
        'Q786820': 100,   # car manufacturer
        'Q167270': 95,    # brand
        'Q4830453': 90,    # business
        'Q43229': 85,     # organization
        
        # Country (alta priorità)
        'Q6256': 100,     # country
        'Q3024240': 95,   # historical country
        'Q7275': 90,      # state
        
        # Person
        'Q5': 100,        # human
        
        # Vehicle types
        'Q1420': 90,      # automobile
        'Q752870': 85,    # motor vehicle
        'Q936518': 80,    # car model
        
        # Event/Competition
        'Q18669875': 100, # competition event
        'Q18649705': 95,  # competition
    }
    
    # Trova il tipo con la priorità più alta
    best_type = None
    best_score = -1
    
    for qid in instance_of_list:
        score = priority_types.get(qid, 0)
        if score > best_score:
            best_score = score
            best_type = qid
    
    # Se non troviamo nessun tipo prioritario, usa il primo della lista
    # (è quello più comune/generale in Wikidata)
    if best_type is None and instance_of_list:
        best_type = instance_of_list[0]
    
    # Fallback al suggerimento dal predicato o default generico
    return best_type if best_type else (predicate_hint if predicate_hint else 'Q35120')

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

def should_use_entity_linking(predicate_str: str) -> bool:
    """
    Determina se un predicato richiede entity linking con Wikidata API.
    
    Ritorna True se il predicato è in iri_target_properties.
    """
    return predicate_str in iri_target_properties

def should_convert_literal_to_iri(predicate_str: str) -> bool:
    """
    Determina se i valori literal di un predicato devono diventare IRI generici (senza entity linking).
    
    Ritorna True se il predicato è in literal_value_to_iri_properties.
    """
    return predicate_str in literal_value_to_iri_properties

def should_keep_literal(predicate_str: str) -> bool:
    """
    Determina se un predicato deve rimanere SEMPRE literal (descrizione + museo specifici).
    """
    return predicate_str in literal_only_properties

def get_donor_predicates():
    """
    Ritorna i predicati per donatore (Wikidata e Schema.org).
    """
    return {
        'wikidata': 'http://www.wikidata.org/prop/direct/P1028',  # donated by
        'schema': 'https://schema.org/sponsor'  # sponsor/donatore
    }

def get_entity_type_for_predicate(predicate_str: str) -> str:
    """
    Suggerisce il tipo di entità Wikidata appropriato per un predicato.
    
    Args:
        predicate_str: URI del predicato (es. 'http://www.wikidata.org/prop/direct/P176')
    
    Returns:
        QID del tipo suggerito (es. 'Q167270' per brand, 'Q6256' per country)
    """
    # Brand/Manufacturer
    if predicate_str in ["http://www.wikidata.org/prop/direct/P176",
                         "http://www.wikidata.org/prop/direct/P1716",
                         "http://schema.org/brand",
                         "https://schema.org/brand",
                         "http://example.org/Marca"]:
        return "Q167270"  # Q167270 = brand (marca)
    
    # Country
    if predicate_str in ["http://www.wikidata.org/prop/direct/P495",
                         "http://schema.org/countryOfOrigin",
                         "http://example.org/Paese"]:
        return "Q6256"  # Q6256 = country (paese)
    
    # Fuel type / power source
    if predicate_str in ["http://www.wikidata.org/prop/direct/P516",
                         "http://www.wikidata.org/prop/direct/P618",
                         "http://schema.org/fuelType",
                         "http://example.org/Alimentazione"]:
        return "Q3541775"  # Q3541775 = motor fuel (combustibile)
    
    # Designer / Person
    if predicate_str in ["http://example.org/Carrozzeria_Designer",
                         "http://schema.org/manufacturer",
                         "http://www.wikidata.org/prop/direct/P287"]:
        return "Q5"  # Q5 = human (persona)
    
    # Default: Thing
    return "Q35120"  # Q35120 = entity (entità generica)

def select_best_type_from_instance_of(instance_of_list, predicate_hint=None):
    """
    Seleziona il tipo più appropriato da instance_of basandosi sul contesto del predicato.
    
    Args:
        instance_of_list: Lista di QID dei tipi (es. ['Q6256', 'Q43229'])
        predicate_hint: QID del tipo suggerito dal predicato (es. 'Q6256' per country)
    
    Returns:
        QID del tipo più appropriato
    """
    if not instance_of_list:
        return predicate_hint or "Q35120"  # Default: entity
    
    # Se troviamo il tipo suggerito esattamente, usalo
    if predicate_hint and predicate_hint in instance_of_list:
        return predicate_hint
    
    # Tipi prioritizzati per specifici contesti
    priority_types = {
        'country': ['Q6256', 'Q3024240', 'Q7275'],  # country, historical country, state
        'brand': ['Q167270', 'Q431289', 'Q783794'],  # brand, company, trademark
        'person': ['Q5'],  # human
        'organization': ['Q43229', 'Q4830453'],  # organization, business
        'fuel': ['Q3541775', 'Q12206'],  # motor fuel, fuel
    }
    
    # Determina contesto dal hint
    context = None
    if predicate_hint == 'Q6256':
        context = 'country'
    elif predicate_hint == 'Q167270':
        context = 'brand'
    elif predicate_hint == 'Q5':
        context = 'person'
    elif predicate_hint == 'Q3541775':
        context = 'fuel'
    
    # Cerca match con tipi prioritizzati
    if context and context in priority_types:
        for prio_type in priority_types[context]:
            if prio_type in instance_of_list:
                return prio_type
    
    # Altrimenti ritorna il primo tipo disponibile
    return instance_of_list[0]

