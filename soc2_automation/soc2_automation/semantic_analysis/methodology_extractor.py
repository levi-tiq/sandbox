#!/usr/bin/env python3
"""
SOC2 Methodology Extractor

Phase 2 of the semantic analysis roadmap: Advanced methodology extraction system.
Uses spaCy NLP pipeline to extract and classify SOC2 testing methodologies.

This module implements:
- Named Entity Recognition (NER) for SOC2 domain-specific entities
- Dependency parsing for action extraction
- Testing verb classification and evidence type identification
- Scope parameter extraction and rigor level assessment

Usage:
    from methodology_extractor import MethodologyExtractor
    
    extractor = MethodologyExtractor()
    methodology = extractor.extract_methodology("Inquired of management regarding access controls...")
"""

import json
import os
import re
from typing import Dict, List, Any, Tuple, Optional, Set
from datetime import datetime
from collections import defaultdict, Counter

try:
    import spacy
    from spacy.tokens import Doc, Token, Span
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("⚠️  Warning: spaCy not available. Please run:")
    print("   pip install spacy")
    print("   python -m spacy download en_core_web_sm")

class SOC2EntityPatterns:
    """SOC2-specific entity patterns and vocabularies"""
    
    def __init__(self):
        # Core testing action verbs (from Phase 1 + expanded)
        self.testing_verbs = {
            'primary': [
                'inquired', 'inspected', 'observed', 'reviewed', 'tested',
                'verified', 'confirmed', 'obtained', 'selected', 'performed',
                'compared', 'evaluated', 'reperformed', 'examined', 'analyzed',
                'validated', 'traced', 'recalculated', 'assessed', 'monitored'
            ],
            'secondary': [
                'documented', 'noted', 'identified', 'determined', 'concluded',
                'found', 'discovered', 'detected', 'located', 'established'
            ]
        }
        
        # Evidence types with detailed subcategories
        self.evidence_types = {
            'documentation': {
                'patterns': [
                    r'\b(document|documentation|report|policy|procedure|manual|guide)\b',
                    r'\b(contract|agreement|charter|standard|framework)\b',
                    r'\b(log|record|registry|database|file|archive)\b',
                    r'\b(certificate|attestation|audit trail|evidence)\b'
                ],
                'subcategories': ['policies', 'procedures', 'logs', 'contracts', 'reports', 'certificates']
            },
            'personnel': {
                'patterns': [
                    r'\b(interview|discussion|inquiry|conversation|meeting)\b',
                    r'\b(personnel|staff|employee|management|administrator)\b',
                    r'\b(responsible party|owner|custodian|stakeholder)\b'
                ],
                'subcategories': ['interviews', 'management_inquiry', 'staff_discussion', 'walkthrough']
            },
            'technical': {
                'patterns': [
                    r'\b(scan|scanning|vulnerability assessment|penetration test)\b',
                    r'\b(configuration|setting|parameter|control)\b',
                    r'\b(system|database|network|server|application)\b',
                    r'\b(access|permission|privilege|authentication|authorization)\b',
                    r'\b(firewall|encryption|backup|monitoring|logging)\b'
                ],
                'subcategories': ['scans', 'configurations', 'access_controls', 'system_tests', 'security_tests']
            },
            'sample': {
                'patterns': [
                    r'\b(sample|sampling|selection|subset)\b',
                    r'\b(transaction|entry|record|item|case)\b',
                    r'\b(user|account|profile|identity)\b',
                    r'\b(request|ticket|incident|exception)\b'
                ],
                'subcategories': ['transactions', 'users', 'requests', 'incidents', 'exceptions']
            },
            'observation': {
                'patterns': [
                    r'\b(observation|walkthrough|demonstration|presentation)\b',
                    r'\b(process|procedure|workflow|operation)\b',
                    r'\b(performance|execution|implementation|operation)\b'
                ],
                'subcategories': ['process_observation', 'system_demonstration', 'walkthrough']
            }
        }
        
        # Scope and scale indicators
        self.scope_patterns = {
            'comprehensive': {
                'patterns': [r'\b(all|every|complete|comprehensive|entire|full|total)\b'],
                'indicators': ['exhaustive', 'complete_coverage', 'all_instances']
            },
            'sample': {
                'patterns': [r'\b(sample|selected|subset|portion|representative)\b'],
                'indicators': ['statistical_sampling', 'judgmental_selection', 'risk_based']
            },
            'specific': {
                'patterns': [r'\b(specific|particular|certain|targeted|focused)\b'],
                'indicators': ['targeted_testing', 'focused_review', 'specific_criteria']
            },
            'judgmental': {
                'patterns': [r'\b(judgmental|risk.based|significant|material|critical)\b'],
                'indicators': ['risk_based_selection', 'materiality_threshold', 'professional_judgment']
            }
        }
        
        # Testing rigor levels
        self.rigor_indicators = {
            'basic': {
                'patterns': [
                    r'\b(inquiry|inquired|asked|discussed)\b',
                    r'\b(review|reviewed|read|examined)\b'
                ],
                'characteristics': ['simple_inquiry', 'document_review', 'basic_discussion']
            },
            'standard': {
                'patterns': [
                    r'\b(tested|performed|validated|verified)\b',
                    r'\b(sample|selection|multiple)\b'
                ],
                'characteristics': ['substantive_testing', 'multiple_evidence', 'validation']
            },
            'comprehensive': {
                'patterns': [
                    r'\b(extensive|comprehensive|detailed|thorough)\b',
                    r'\b(reperformed|recalculated|traced|vouched)\b'
                ],
                'characteristics': ['extensive_testing', 'detailed_analysis', 'independent_verification']
            }
        }
        
        # SOC2 Trust Services Criteria entities
        self.soc2_entities = {
            'criteria': ['CC', 'A', 'CA', 'PI', 'P'],
            'control_families': [
                'Common Criteria', 'Additional Criteria', 'Confidentiality',
                'Processing Integrity', 'Privacy', 'Availability'
            ],
            'processes': [
                'ITGC', 'ITAC', 'Change Management', 'Access Management',
                'System Operations', 'Logical Access', 'Physical Access'
            ]
        }

class MethodologyExtractor:
    """Advanced methodology extraction using spaCy NLP"""
    
    def __init__(self, model_name: str = "en_core_web_sm"):
        """Initialize methodology extractor with spaCy model"""
        if not SPACY_AVAILABLE:
            raise ImportError("spaCy not available. Please install spacy and download en_core_web_sm model.")
        
        self.model_name = model_name
        self.nlp = None
        self.matcher = None
        self.patterns = SOC2EntityPatterns()
        
        # Analysis results cache
        self.analysis_cache = {}
        
    def _load_model(self):
        """Load spaCy model with custom SOC2 patterns"""
        if self.nlp is None:
            try:
                print(f"🔧 Loading spaCy model: {self.model_name}")
                self.nlp = spacy.load(self.model_name)
                
                # Add custom SOC2 patterns to matcher
                self._add_custom_patterns()
                
                print("✅ spaCy model loaded with SOC2 patterns")
            except OSError as e:
                print(f"❌ Failed to load spaCy model: {e}")
                print("   Try: python -m spacy download en_core_web_sm")
                raise
    
    def _add_custom_patterns(self):
        """Add custom SOC2-specific patterns to spaCy pipeline"""
        from spacy.matcher import Matcher
        
        # Initialize matcher
        self.matcher = Matcher(self.nlp.vocab)
        
        # Add testing verb patterns
        for verb_type, verbs in self.patterns.testing_verbs.items():
            for verb in verbs:
                pattern = [{"LOWER": verb, "POS": "VERB"}]
                self.matcher.add(f"TESTING_VERB_{verb_type.upper()}", [pattern])
        
        # Add SOC2 criteria patterns
        for criterion in self.patterns.soc2_entities['criteria']:
            pattern = [{"TEXT": {"REGEX": f"^{criterion}\\d+(\\.\\d+)*$"}}]
            self.matcher.add("SOC2_CRITERION", [pattern])
        
        # Note: Store matcher as instance variable instead of pipeline component
    
    def extract_methodology(self, text: str) -> Dict[str, Any]:
        """
        Extract comprehensive methodology information from SOC2 test description
        
        Args:
            text: SOC2 test description text
            
        Returns:
            Dictionary with detailed methodology analysis
        """
        if not text or not text.strip():
            return self._empty_methodology_result()
        
        # Load model if needed
        self._load_model()
        
        # Check cache first
        cache_key = hash(text.strip())
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]
        
        print(f"🔍 Extracting methodology from: {text[:100]}...")
        
        # Process text with spaCy
        doc = self.nlp(text)
        
        # Extract methodology components
        methodology = {
            'original_text': text,
            'text_length': len(text),
            'word_count': len(text.split()),
            
            # Core methodology components
            'testing_actions': self._extract_testing_actions(doc),
            'evidence_types': self._extract_evidence_types(doc),
            'scope_analysis': self._extract_scope_analysis(doc),
            'rigor_assessment': self._assess_testing_rigor(doc),
            
            # Advanced NLP analysis
            'entities': self._extract_named_entities(doc),
            'dependencies': self._analyze_dependencies(doc),
            'temporal_references': self._extract_temporal_info(doc),
            
            # SOC2-specific analysis
            'soc2_elements': self._extract_soc2_elements(doc),
            'compliance_indicators': self._extract_compliance_indicators(doc),
            
            # Methodology classification
            'methodology_type': self._classify_methodology_type(doc),
            'complexity_score': self._calculate_complexity_score(doc),
            'automation_feasibility': self._assess_automation_feasibility(doc),
            
            # Metadata
            'analysis_timestamp': datetime.now().isoformat(),
            'processing_metadata': {
                'sentence_count': len(list(doc.sents)),
                'token_count': len(doc),
                'pos_tags': self._get_pos_summary(doc)
            }
        }
        
        # Cache result
        self.analysis_cache[cache_key] = methodology
        
        return methodology
    
    def _extract_testing_actions(self, doc: Doc) -> Dict[str, Any]:
        """Extract testing actions and verbs"""
        actions = {
            'primary_actions': [],
            'secondary_actions': [],
            'action_sequence': [],
            'action_objects': [],
            'action_modifiers': []
        }
        
        # Find all testing verbs
        for token in doc:
            if token.pos_ == "VERB" and not token.is_stop:
                lemma = token.lemma_.lower()
                
                # Classify verb type
                if lemma in self.patterns.testing_verbs['primary']:
                    actions['primary_actions'].append({
                        'verb': lemma,
                        'text': token.text,
                        'position': token.i,
                        'confidence': 'high',
                        'dependencies': [child.text for child in token.children]
                    })
                elif lemma in self.patterns.testing_verbs['secondary']:
                    actions['secondary_actions'].append({
                        'verb': lemma,
                        'text': token.text,
                        'position': token.i,
                        'confidence': 'medium',
                        'dependencies': [child.text for child in token.children]
                    })
                
                # Extract direct objects
                for child in token.children:
                    if child.dep_ == "dobj":
                        actions['action_objects'].append({
                            'object': child.text,
                            'action': lemma,
                            'position': child.i
                        })
        
        # Determine primary methodology
        if actions['primary_actions']:
            actions['primary_methodology'] = actions['primary_actions'][0]['verb']
        else:
            actions['primary_methodology'] = 'unknown'
        
        return actions
    
    def _extract_evidence_types(self, doc: Doc) -> Dict[str, Any]:
        """Extract and classify evidence types"""
        evidence = {
            'types_found': [],
            'detailed_evidence': [],
            'evidence_strength': 'unknown',
            'evidence_sources': []
        }
        
        text_lower = doc.text.lower()
        
        # Check each evidence type
        for evidence_type, type_data in self.patterns.evidence_types.items():
            type_matches = []
            
            for pattern in type_data['patterns']:
                matches = re.finditer(pattern, text_lower, re.IGNORECASE)
                for match in matches:
                    type_matches.append({
                        'match': match.group(),
                        'start': match.start(),
                        'end': match.end(),
                        'subcategory': self._classify_evidence_subcategory(match.group(), type_data['subcategories'])
                    })
            
            if type_matches:
                evidence['types_found'].append(evidence_type)
                evidence['detailed_evidence'].append({
                    'type': evidence_type,
                    'matches': type_matches,
                    'count': len(type_matches)
                })
        
        # Assess evidence strength
        evidence['evidence_strength'] = self._assess_evidence_strength(evidence['types_found'])
        
        return evidence
    
    def _extract_scope_analysis(self, doc: Doc) -> Dict[str, Any]:
        """Analyze testing scope and coverage"""
        scope = {
            'scope_type': 'standard',
            'scope_indicators': [],
            'sample_size_mentioned': False,
            'sample_size_value': None,
            'time_period_mentioned': False,
            'coverage_level': 'partial'
        }
        
        text_lower = doc.text.lower()
        
        # Check scope patterns
        for scope_type, scope_data in self.patterns.scope_patterns.items():
            for pattern in scope_data['patterns']:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    scope['scope_type'] = scope_type
                    scope['scope_indicators'].extend(scope_data['indicators'])
                    break
        
        # Extract sample sizes
        sample_patterns = [
            r'\b(\d+)\s+(samples?|items?|transactions?|users?|controls?)\b',
            r'\bsample\s+of\s+(\d+)\b',
            r'\b(\d+)\s+out\s+of\s+(\d+)\b'
        ]
        
        for pattern in sample_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                scope['sample_size_mentioned'] = True
                scope['sample_size_value'] = int(match.group(1))
                break
        
        # Detect time periods
        time_patterns = [
            r'\b(during|for|from|through|period)\s+.*?\d{4}\b',
            r'\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b'
        ]
        
        for pattern in time_patterns:
            if re.search(pattern, text_lower):
                scope['time_period_mentioned'] = True
                break
        
        return scope
    
    def _assess_testing_rigor(self, doc: Doc) -> Dict[str, Any]:
        """Assess the rigor and depth of testing"""
        rigor = {
            'rigor_level': 'standard',
            'rigor_score': 0.5,
            'rigor_indicators': [],
            'testing_depth': 'moderate',
            'independence_level': 'standard'
        }
        
        text_lower = doc.text.lower()
        rigor_scores = []
        
        # Check rigor indicators
        for level, level_data in self.patterns.rigor_indicators.items():
            level_score = 0
            found_indicators = []
            
            for pattern in level_data['patterns']:
                matches = len(re.findall(pattern, text_lower, re.IGNORECASE))
                if matches > 0:
                    level_score += matches
                    found_indicators.extend(level_data['characteristics'])
            
            if level_score > 0:
                rigor_scores.append((level, level_score, found_indicators))
        
        # Determine overall rigor level
        if rigor_scores:
            rigor_scores.sort(key=lambda x: x[1], reverse=True)
            rigor['rigor_level'] = rigor_scores[0][0]
            rigor['rigor_indicators'] = rigor_scores[0][2]
            
            # Calculate numeric score (0-1)
            if rigor['rigor_level'] == 'basic':
                rigor['rigor_score'] = 0.3
            elif rigor['rigor_level'] == 'comprehensive':
                rigor['rigor_score'] = 0.9
            else:
                rigor['rigor_score'] = 0.6
        
        return rigor
    
    def _extract_named_entities(self, doc: Doc) -> List[Dict[str, Any]]:
        """Extract named entities with SOC2 context"""
        entities = []
        
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'label': ent.label_,
                'description': spacy.explain(ent.label_),
                'start': ent.start_char,
                'end': ent.end_char,
                'confidence': getattr(ent, 'confidence', None)
            })
        
        return entities
    
    def _analyze_dependencies(self, doc: Doc) -> Dict[str, Any]:
        """Analyze syntactic dependencies for methodology extraction"""
        dependencies = {
            'root_verbs': [],
            'subject_verb_object': [],
            'prepositional_phrases': [],
            'dependency_tree': []
        }
        
        # Find root verbs (main actions)
        for token in doc:
            if token.dep_ == "ROOT" and token.pos_ == "VERB":
                dependencies['root_verbs'].append({
                    'verb': token.lemma_,
                    'text': token.text,
                    'subjects': [child.text for child in token.children if child.dep_ in ["nsubj", "nsubjpass"]],
                    'objects': [child.text for child in token.children if child.dep_ in ["dobj", "pobj"]]
                })
        
        # Extract subject-verb-object relationships
        for token in doc:
            if token.pos_ == "VERB":
                subjects = [child for child in token.children if child.dep_ in ["nsubj", "nsubjpass"]]
                objects = [child for child in token.children if child.dep_ in ["dobj", "pobj"]]
                
                if subjects and objects:
                    dependencies['subject_verb_object'].append({
                        'subject': subjects[0].text,
                        'verb': token.lemma_,
                        'object': objects[0].text
                    })
        
        return dependencies
    
    def _extract_temporal_info(self, doc: Doc) -> Dict[str, Any]:
        """Extract temporal and time-related information"""
        temporal = {
            'time_expressions': [],
            'dates_mentioned': [],
            'duration_indicators': [],
            'frequency_indicators': []
        }
        
        # Use spaCy's built-in date/time recognition
        for ent in doc.ents:
            if ent.label_ in ["DATE", "TIME", "CARDINAL"]:
                temporal['time_expressions'].append({
                    'text': ent.text,
                    'label': ent.label_,
                    'start': ent.start_char,
                    'end': ent.end_char
                })
        
        return temporal
    
    def _extract_soc2_elements(self, doc: Doc) -> Dict[str, Any]:
        """Extract SOC2-specific elements and terminology"""
        soc2_elements = {
            'criteria_mentioned': [],
            'trust_services': [],
            'control_activities': [],
            'soc2_terminology': []
        }
        
        text_upper = doc.text.upper()
        
        # Find SOC2 criteria (CC1.1, A1.2, etc.)
        criteria_pattern = r'\b([A-Z]{1,2})\s*(\d+)\.(\d+)\b'
        criteria_matches = re.finditer(criteria_pattern, text_upper)
        
        for match in criteria_matches:
            soc2_elements['criteria_mentioned'].append({
                'full_criterion': match.group(),
                'category': match.group(1),
                'number': f"{match.group(2)}.{match.group(3)}"
            })
        
        return soc2_elements
    
    def _extract_compliance_indicators(self, doc: Doc) -> Dict[str, Any]:
        """Extract compliance and attestation indicators"""
        compliance = {
            'compliance_verbs': [],
            'attestation_language': [],
            'exception_indicators': [],
            'deficiency_indicators': []
        }
        
        # Compliance-related verbs
        compliance_verbs = [
            'complies', 'complied', 'compliance', 'adherence', 'conforms',
            'meets', 'satisfies', 'fulfills', 'achieves', 'maintains'
        ]
        
        for token in doc:
            if token.lemma_.lower() in compliance_verbs:
                compliance['compliance_verbs'].append(token.text)
        
        return compliance
    
    def _classify_methodology_type(self, doc: Doc) -> Dict[str, Any]:
        """Classify the overall methodology type"""
        # Based on extracted actions and evidence
        actions = self._extract_testing_actions(doc)
        evidence = self._extract_evidence_types(doc)
        
        methodology_type = {
            'primary_type': 'unknown',
            'secondary_types': [],
            'confidence': 0.0,
            'classification_basis': []
        }
        
        # Classification logic based on evidence and actions
        if 'technical' in evidence['types_found'] and actions['primary_actions']:
            methodology_type['primary_type'] = 'technical_testing'
            methodology_type['confidence'] = 0.8
        elif 'personnel' in evidence['types_found']:
            methodology_type['primary_type'] = 'inquiry_based'
            methodology_type['confidence'] = 0.7
        elif 'documentation' in evidence['types_found']:
            methodology_type['primary_type'] = 'document_review'
            methodology_type['confidence'] = 0.6
        elif 'sample' in evidence['types_found']:
            methodology_type['primary_type'] = 'sample_testing'
            methodology_type['confidence'] = 0.75
        
        return methodology_type
    
    def _calculate_complexity_score(self, doc: Doc) -> float:
        """Calculate methodology complexity score (0-1)"""
        complexity_factors = {
            'sentence_length': len(doc.text.split()) / 50.0,  # Normalize by typical length
            'technical_terms': len([token for token in doc if token.pos_ == "NOUN" and len(token.text) > 6]) / len(doc),
            'action_diversity': 0,
            'evidence_types': 0
        }
        
        # Normalize and weight factors
        complexity_score = (
            min(complexity_factors['sentence_length'], 1.0) * 0.2 +
            complexity_factors['technical_terms'] * 0.3 +
            complexity_factors['action_diversity'] * 0.25 +
            complexity_factors['evidence_types'] * 0.25
        )
        
        return min(complexity_score, 1.0)
    
    def _assess_automation_feasibility(self, doc: Doc) -> Dict[str, Any]:
        """Assess how feasible this methodology is for automation"""
        feasibility = {
            'feasibility_score': 0.5,
            'feasibility_level': 'medium',
            'automation_barriers': [],
            'automation_opportunities': [],
            'template_potential': False
        }
        
        # Factors that increase automation feasibility
        positive_factors = [
            ('standard_verbs', self._has_standard_testing_verbs(doc)),
            ('clear_structure', self._has_clear_structure(doc)),
            ('measurable_criteria', self._has_measurable_criteria(doc)),
            ('repeatable_process', self._is_repeatable_process(doc))
        ]
        
        # Factors that decrease automation feasibility
        negative_factors = [
            ('high_judgment', self._requires_high_judgment(doc)),
            ('complex_language', self._has_complex_language(doc)),
            ('unique_circumstances', self._has_unique_circumstances(doc))
        ]
        
        # Calculate feasibility score
        positive_score = sum([0.25 for factor, result in positive_factors if result])
        negative_score = sum([0.2 for factor, result in negative_factors if result])
        
        feasibility['feasibility_score'] = max(0, min(1, 0.5 + positive_score - negative_score))
        
        # Classify feasibility level
        if feasibility['feasibility_score'] >= 0.7:
            feasibility['feasibility_level'] = 'high'
            feasibility['template_potential'] = True
        elif feasibility['feasibility_score'] >= 0.4:
            feasibility['feasibility_level'] = 'medium'
        else:
            feasibility['feasibility_level'] = 'low'
        
        return feasibility
    
    def _classify_evidence_subcategory(self, match_text: str, subcategories: List[str]) -> str:
        """Classify evidence into subcategory"""
        # Simple keyword-based classification
        match_lower = match_text.lower()
        
        for subcategory in subcategories:
            if any(word in match_lower for word in subcategory.split('_')):
                return subcategory
        
        return subcategories[0] if subcategories else 'general'
    
    def _assess_evidence_strength(self, evidence_types: List[str]) -> str:
        """Assess overall evidence strength"""
        if len(evidence_types) >= 3:
            return 'strong'
        elif len(evidence_types) == 2:
            return 'moderate'
        elif len(evidence_types) == 1:
            return 'basic'
        else:
            return 'insufficient'
    
    def _get_pos_summary(self, doc: Doc) -> Dict[str, int]:
        """Get part-of-speech tag summary"""
        pos_counts = Counter(token.pos_ for token in doc)
        return dict(pos_counts.most_common(10))
    
    def _has_standard_testing_verbs(self, doc: Doc) -> bool:
        """Check if text uses standard testing verbs"""
        text_lower = doc.text.lower()
        standard_verbs = self.patterns.testing_verbs['primary']
        return any(verb in text_lower for verb in standard_verbs[:5])
    
    def _has_clear_structure(self, doc: Doc) -> bool:
        """Check if text has clear, structured language"""
        # Simple heuristic: check for clear sentence structure
        return len(list(doc.sents)) <= 3 and len(doc.text.split()) < 100
    
    def _has_measurable_criteria(self, doc: Doc) -> bool:
        """Check if methodology has measurable criteria"""
        # Look for numbers, percentages, specific quantities
        return bool(re.search(r'\b\d+\b', doc.text))
    
    def _is_repeatable_process(self, doc: Doc) -> bool:
        """Check if process appears repeatable"""
        # Look for standard process language
        process_words = ['procedure', 'process', 'method', 'approach', 'technique']
        text_lower = doc.text.lower()
        return any(word in text_lower for word in process_words)
    
    def _requires_high_judgment(self, doc: Doc) -> bool:
        """Check if methodology requires high professional judgment"""
        judgment_words = ['judgment', 'assessment', 'evaluation', 'consideration', 'professional']
        text_lower = doc.text.lower()
        return any(word in text_lower for word in judgment_words)
    
    def _has_complex_language(self, doc: Doc) -> bool:
        """Check if language is overly complex"""
        # Heuristic: long sentences, complex words
        avg_word_length = sum(len(token.text) for token in doc if token.is_alpha) / len([token for token in doc if token.is_alpha])
        return avg_word_length > 6 or len(doc.text.split()) > 150
    
    def _has_unique_circumstances(self, doc: Doc) -> bool:
        """Check if methodology involves unique circumstances"""
        unique_words = ['specific', 'unique', 'particular', 'special', 'custom', 'tailored']
        text_lower = doc.text.lower()
        return sum(text_lower.count(word) for word in unique_words) > 2
    
    def _empty_methodology_result(self) -> Dict[str, Any]:
        """Return empty methodology result for invalid input"""
        return {
            'original_text': '',
            'text_length': 0,
            'word_count': 0,
            'testing_actions': {'primary_actions': [], 'secondary_actions': []},
            'evidence_types': {'types_found': [], 'evidence_strength': 'insufficient'},
            'scope_analysis': {'scope_type': 'unknown'},
            'rigor_assessment': {'rigor_level': 'unknown', 'rigor_score': 0},
            'methodology_type': {'primary_type': 'unknown', 'confidence': 0},
            'complexity_score': 0,
            'automation_feasibility': {'feasibility_level': 'unknown', 'template_potential': False},
            'analysis_timestamp': datetime.now().isoformat(),
            'error': 'invalid_input'
        }
    
    def analyze_methodology_patterns(self, variance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze methodology patterns from variance data structure
        Bridges the gap between control_variance_analyzer and methodology extractor
        """
        print("🔧 Analyzing methodology patterns from variance data...")
        
        methodology_analysis = {
            'analysis_timestamp': datetime.now().isoformat(),
            'methodology_analysis': {},
            'overall_patterns': {}
        }
        
        # Extract variance analysis from the input data
        variance_analysis = variance_data.get('variance_analysis', {})
        
        processed_controls = 0
        for control_key, control_data in variance_analysis.items():
            try:
                # Get company tests from control data
                company_tests = control_data.get('company_tests', {})
                
                if not company_tests:
                    continue
                
                # Create methodology analysis for this control
                control_methodology = {
                    'text_methodologies': {}
                }
                
                # Process each company's tests
                for company, tests in company_tests.items():
                    if tests:  # Ensure tests list is not empty
                        # Take the first test for analysis (or combine multiple if needed)
                        primary_test = tests[0] if isinstance(tests, list) else str(tests)
                        
                        # Extract methodology for this text
                        methodology = self.extract_methodology(primary_test)
                        control_methodology['text_methodologies'][company] = methodology
                
                # Store methodology analysis for this control
                methodology_analysis['methodology_analysis'][control_key] = control_methodology
                processed_controls += 1
                
                if processed_controls % 50 == 0:
                    print(f"   Processed {processed_controls} controls...")
                
            except Exception as e:
                print(f"   Warning: Failed to process control {control_key}: {e}")
                continue
        
        print(f"✅ Methodology pattern analysis complete for {processed_controls} controls")
        return methodology_analysis
    
    def analyze_multiple_texts(self, texts: List[str]) -> Dict[str, Any]:
        """Analyze multiple text descriptions and generate comparative insights"""
        print(f"🔍 Analyzing methodology for {len(texts)} test descriptions...")
        
        results = []
        for i, text in enumerate(texts):
            print(f"   Processing {i+1}/{len(texts)}")
            methodology = self.extract_methodology(text)
            results.append(methodology)
        
        # Generate comparative analysis
        comparative_analysis = self._generate_comparative_analysis(results)
        
        return {
            'individual_results': results,
            'comparative_analysis': comparative_analysis,
            'analysis_metadata': {
                'total_texts': len(texts),
                'analysis_timestamp': datetime.now().isoformat(),
                'model_used': self.model_name
            }
        }
    
    def _generate_comparative_analysis(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comparative analysis across multiple methodology extractions"""
        
        # Aggregate methodology types
        methodology_types = [r['methodology_type']['primary_type'] for r in results if r['methodology_type']['primary_type'] != 'unknown']
        
        # Aggregate evidence types
        all_evidence_types = []
        for r in results:
            all_evidence_types.extend(r['evidence_types']['types_found'])
        
        # Aggregate rigor levels
        rigor_levels = [r['rigor_assessment']['rigor_level'] for r in results if r['rigor_assessment']['rigor_level'] != 'unknown']
        
        # Calculate automation potential
        automation_scores = [r['automation_feasibility']['feasibility_score'] for r in results]
        
        return {
            'methodology_distribution': dict(Counter(methodology_types)),
            'evidence_type_frequency': dict(Counter(all_evidence_types)),
            'rigor_distribution': dict(Counter(rigor_levels)),
            'automation_potential': {
                'mean_feasibility': sum(automation_scores) / len(automation_scores) if automation_scores else 0,
                'high_automation_potential': len([s for s in automation_scores if s >= 0.7]),
                'low_automation_potential': len([s for s in automation_scores if s < 0.4])
            },
            'complexity_analysis': {
                'mean_complexity': sum(r['complexity_score'] for r in results) / len(results),
                'complexity_range': [min(r['complexity_score'] for r in results), max(r['complexity_score'] for r in results)]
            }
        }

def main():
    """Main execution function for standalone usage"""
    print("🔧 SOC2 Methodology Extractor - Phase 2 Implementation")
    print("=" * 60)
    
    try:
        # Initialize extractor
        extractor = MethodologyExtractor()
        
        # Test with sample SOC2 text
        sample_texts = [
            "Inquired of management regarding the access control procedures for the period from 01/01/2024 to 12/31/2024 and obtained supporting documentation to verify implementation.",
            "Inspected a sample of 25 user access provisioning requests to determine whether proper approval was obtained from authorized personnel prior to granting access.",
            "Performed vulnerability scans on 5 selected servers and reviewed the scan results to identify any critical vulnerabilities or misconfigurations.",
            "Observed the performance of the backup and recovery procedures and reviewed logs to confirm that backups were completed successfully during the testing period."
        ]
        
        print(f"🧪 Testing with {len(sample_texts)} sample SOC2 descriptions...")
        
        # Analyze sample texts
        results = extractor.analyze_multiple_texts(sample_texts)
        
        print(f"\n📊 METHODOLOGY EXTRACTION SUMMARY:")
        print("=" * 50)
        
        comparative = results['comparative_analysis']
        
        print(f"🎯 Methodology Types Found:")
        for method_type, count in comparative['methodology_distribution'].items():
            print(f"   {method_type}: {count}")
        
        print(f"\n📋 Evidence Types Frequency:")
        for evidence_type, count in comparative['evidence_type_frequency'].items():
            print(f"   {evidence_type}: {count}")
        
        print(f"\n🎚️ Testing Rigor Distribution:")
        for rigor_level, count in comparative['rigor_distribution'].items():
            print(f"   {rigor_level}: {count}")
        
        automation = comparative['automation_potential']
        print(f"\n🤖 Automation Potential:")
        print(f"   Mean feasibility: {automation['mean_feasibility']:.2f}")
        print(f"   High potential: {automation['high_automation_potential']} texts")
        print(f"   Low potential: {automation['low_automation_potential']} texts")
        
        complexity = comparative['complexity_analysis']
        print(f"\n📈 Complexity Analysis:")
        print(f"   Mean complexity: {complexity['mean_complexity']:.2f}")
        print(f"   Range: {complexity['complexity_range'][0]:.2f} - {complexity['complexity_range'][1]:.2f}")
        
        print(f"\n✅ Phase 2 methodology extraction complete!")
        print(f"💡 Next: Integrate with semantic analysis pipeline")
        
    except Exception as e:
        print(f"❌ Methodology extraction failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()