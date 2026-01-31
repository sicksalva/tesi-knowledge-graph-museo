# Changelog

## [1.0.0] - 2026-01-31

### Added
- Initial project structure for museum knowledge graph
- CSV data cleaning script with completeness analysis
- SPARQL transformation query for RDF generation
- Post-processing filter for empty values
- Comprehensive documentation and project log

### Features
- **Data Processing**: Clean 163 vehicles from 29 to 11 semantic columns
- **RDF Generation**: Transform CSV to N-Triples format (287KB output)
- **Quality Control**: Zero empty values in final knowledge graph
- **Rich Semantics**: 11 properties per vehicle including technical specifications

### Technical Details
- **Input**: museo.csv (164 rows × 29 columns)
- **Output**: museo_cleaned.csv (163 rows × 11 columns)
- **RDF Triples**: ~2,500 semantic assertions
- **Completeness**: Optimized from 0.6% (carrozzeria) to 75-80% (technical data)

### Documentation
- Complete project log with step-by-step process
- Technical choices documentation
- Examples and best practices for knowledge graph creation

---

*For detailed information, see [progetto_log.md](notes/md/progetto_log.md)*