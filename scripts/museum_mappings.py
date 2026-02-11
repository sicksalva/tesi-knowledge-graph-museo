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
    "http://example.org/museum/floorLevel",
    "http://example.org/museum/section", 
    "http://example.org/N_inventario",
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
    
    # BRAND/MARCA (sempre literal come specificato dall'utente)
    "http://example.org/Marca",
    "http://schema.org/brand",                   # brand
    "https://schema.org/brand",                  # brand (HTTPS version)
    "http://www.wikidata.org/prop/direct/P176",  # manufacturer
    "http://www.wikidata.org/prop/direct/P1716", # brand
    
    # DATI NUMERICI TECNICI (seguendo tabella + mappings.csv)
    "http://example.org/Modello",
    "http://schema.org/model",                    # model name
    "https://schema.org/model",                   # model name (HTTPS)
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