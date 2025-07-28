
"""
LangChain-based clause processing for advanced clause extraction.
Uses LLM agents for intelligent clause identification and analysis.
"""

import logging
import json
from typing import Dict, List, Any, Optional
from langchain.agents import initialize_agent, AgentType
from langchain.tools import BaseTool
from langchain.llms.base import LLM
from langchain.schema import AgentAction, AgentFinish
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import sys
import os

# Add common to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from common.config import config
from common.database import db_connection

logger = logging.getLogger(__name__)


class SnowflakeLLM(LLM):
    """Custom LLM wrapper for Snowflake Cortex."""
    
    def __init__(self):
        super().__init__()
        self.model_name = config.snowflake.llm_model
        self.db_connection = db_connection
    
    @property
    def _llm_type(self) -> str:
        return "snowflake_cortex"
    
    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        """Call Snowflake Cortex LLM."""
        try:
            # Escape single quotes in prompt
            escaped_prompt = prompt.replace("'", "''")
            
            query = f"""
            SELECT SNOWFLAKE.CORTEX.COMPLETE('{self.model_name}', '{escaped_prompt}') as response
            """
            
            result = self.db_connection.execute_query(query)
            if result and len(result) > 0:
                return result[0]['RESPONSE']
            else:
                return "Error: No response from Snowflake Cortex"
                
        except Exception as e:
            logger.error(f"Snowflake LLM call error: {e}")
            return f"Error: {str(e)}"


class ClauseExtractionTool(BaseTool):
    """Tool for extracting clauses from document text."""
    
    name = "clause_extractor"
    description = "Extract individual clauses from contract or legal document text"
    
    def _run(self, text: str) -> str:
        """Extract clauses from text."""
        try:
            # Simple clause extraction based on common patterns
            clauses = self._extract_clauses_by_pattern(text)
            
            return json.dumps({
                'clauses': clauses,
                'total_clauses': len(clauses)
            })
            
        except Exception as e:
            return f"Error extracting clauses: {str(e)}"
    
    async def _arun(self, text: str) -> str:
        """Async version of clause extraction."""
        return self._run(text)
    
    def _extract_clauses_by_pattern(self, text: str) -> List[Dict[str, Any]]:
        """Extract clauses using pattern matching."""
        import re
        
        clauses = []
        
        # Split text into potential clauses based on common patterns
        # Pattern 1: Numbered clauses (1., 2., etc.)
        numbered_pattern = r'(\d+\.\s+[^0-9]+?)(?=\d+\.\s+|\Z)'
        numbered_matches = re.findall(numbered_pattern, text, re.DOTALL)
        
        for i, match in enumerate(numbered_matches):
            clauses.append({
                'clause_number': f"{i+1}",
                'text': match.strip(),
                'extraction_method': 'numbered_pattern',
                'section_reference': f"Clause {i+1}"
            })
        
        # Pattern 2: Lettered clauses (a), b), etc.)
        lettered_pattern = r'([a-z]\)\s+[^a-z\)]+?)(?=[a-z]\)\s+|\Z)'
        lettered_matches = re.findall(lettered_pattern, text, re.DOTALL)
        
        for i, match in enumerate(lettered_matches):
            letter = chr(ord('a') + i)
            clauses.append({
                'clause_number': f"{letter})",
                'text': match.strip(),
                'extraction_method': 'lettered_pattern',
                'section_reference': f"Clause {letter})"
            })
        
        # Pattern 3: Section headers
        section_pattern = r'((?:SECTION|Section)\s+\d+[^S]*?)(?=(?:SECTION|Section)\s+\d+|\Z)'
        section_matches = re.findall(section_pattern, text, re.DOTALL)
        
        for i, match in enumerate(section_matches):
            clauses.append({
                'clause_number': f"S{i+1}",
                'text': match.strip(),
                'extraction_method': 'section_pattern',
                'section_reference': f"Section {i+1}"
            })
        
        # If no patterns found, split by paragraphs
        if not clauses:
            paragraphs = [p.strip() for p in text.split('\n\n') if p.strip() and len(p.strip()) > 50]
            for i, paragraph in enumerate(paragraphs):
                clauses.append({
                    'clause_number': f"P{i+1}",
                    'text': paragraph,
                    'extraction_method': 'paragraph_split',
                    'section_reference': f"Paragraph {i+1}"
                })
        
        return clauses


class ClauseClassificationTool(BaseTool):
    """Tool for classifying clause types."""
    
    name = "clause_classifier"
    description = "Classify contract clauses into compliance categories"
    
    def _run(self, clause_text: str) -> str:
        """Classify clause type."""
        try:
            # Simple keyword-based classification
            classification = self._classify_clause_simple(clause_text)
            return json.dumps(classification)
            
        except Exception as e:
            return f"Error classifying clause: {str(e)}"
    
    async def _arun(self, clause_text: str) -> str:
        """Async version of clause classification."""
        return self._run(clause_text)
    
    def _classify_clause_simple(self, text: str) -> Dict[str, Any]:
        """Simple keyword-based clause classification."""
        text_lower = text.lower()
        
        # Classification keywords
        categories = {
            'safety_compliance': [
                'safety', 'health', 'hazard', 'risk', 'accident', 'injury',
                'emergency', 'protective equipment', 'safety management'
            ],
            'environmental_compliance': [
                'environmental', 'pollution', 'waste', 'emissions', 'water',
                'air quality', 'rehabilitation', 'biodiversity'
            ],
            'operational_compliance': [
                'operation', 'production', 'mining', 'extraction', 'processing',
                'equipment', 'maintenance', 'inspection'
            ],
            'commercial_terms': [
                'payment', 'price', 'cost', 'invoice', 'delivery', 'supply',
                'warranty', 'liability', 'insurance'
            ],
            'legal_provisions': [
                'contract', 'agreement', 'breach', 'termination', 'dispute',
                'governing law', 'jurisdiction', 'arbitration'
            ]
        }
        
        scores = {}
        for category, keywords in categories.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[category] = score
        
        # Determine primary classification
        if scores:
            primary_type = max(scores, key=scores.get)
            max_score = scores[primary_type]
            confidence = min(1.0, max_score / 5.0)  # Normalize to 0-1
        else:
            primary_type = 'unknown'
            confidence = 0.0
        
        return {
            'primary_type': primary_type,
            'confidence': confidence,
            'scores': scores,
            'word_count': len(text.split())
        }


class LangChainClauseProcessor:
    """LangChain-based clause processor using Snowflake Cortex."""
    
    def __init__(self):
        self.llm = SnowflakeLLM()
        self.tools = [
            ClauseExtractionTool(),
            ClauseClassificationTool()
        ]
        
        # Initialize agent
        self.agent = initialize_agent(
            tools=self.tools,
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            max_iterations=3,
            early_stopping_method="generate"
        )
        
        # Clause extraction prompt
        self.extraction_prompt = PromptTemplate(
            input_variables=["document_text"],
            template="""
            You are an expert legal document analyzer specializing in Australian mining compliance.
            
            Analyze the following document text and extract individual clauses that relate to:
            1. Safety compliance and work health & safety requirements
            2. Environmental compliance and protection obligations
            3. Operational compliance and mining regulations
            4. Commercial terms and conditions
            5. Legal provisions and contractual obligations
            
            For each clause you identify, provide:
            - The full text of the clause
            - A brief title or description
            - The clause type/category
            - Any section or clause number references
            - Key compliance requirements mentioned
            
            Document text:
            {document_text}
            
            Please extract and analyze the clauses systematically.
            """
        )
        
        # Create extraction chain
        self.extraction_chain = LLMChain(
            llm=self.llm,
            prompt=self.extraction_prompt
        )
    
    def extract_clauses(self, document_text: str) -> Dict[str, Any]:
        """Extract clauses from document text using LangChain agent."""
        try:
            if not document_text or len(document_text.strip()) < 100:
                return {
                    'clauses': [],
                    'total_clauses': 0,
                    'error': 'Document text too short for clause extraction'
                }
            
            # Use the extraction chain for initial processing
            extraction_result = self.extraction_chain.run(document_text=document_text[:4000])  # Limit text length
            
            # Parse the LLM response to extract structured clause data
            clauses = self._parse_llm_extraction_result(extraction_result, document_text)
            
            # If LLM extraction didn't work well, fall back to pattern-based extraction
            if len(clauses) < 2:
                logger.warning("LLM extraction yielded few results, falling back to pattern-based extraction")
                fallback_clauses = self._fallback_clause_extraction(document_text)
                clauses.extend(fallback_clauses)
            
            # Classify each clause
            for clause in clauses:
                classification = self._classify_clause_with_llm(clause['text'])
                clause.update(classification)
            
            return {
                'clauses': clauses,
                'total_clauses': len(clauses),
                'extraction_method': 'langchain_with_snowflake_cortex',
                'processing_notes': 'Used LLM for intelligent clause extraction and classification'
            }
            
        except Exception as e:
            logger.error(f"LangChain clause extraction error: {e}")
            # Fallback to pattern-based extraction
            return self._fallback_clause_extraction(document_text)
    
    def _parse_llm_extraction_result(self, llm_result: str, original_text: str) -> List[Dict[str, Any]]:
        """Parse LLM extraction result into structured clause data."""
        clauses = []
        
        try:
            # Try to parse as JSON first
            if llm_result.strip().startswith('{') or llm_result.strip().startswith('['):
                parsed_result = json.loads(llm_result)
                if isinstance(parsed_result, dict) and 'clauses' in parsed_result:
                    return parsed_result['clauses']
                elif isinstance(parsed_result, list):
                    return parsed_result
        except json.JSONDecodeError:
            pass
        
        # Parse text-based response
        lines = llm_result.split('\n')
        current_clause = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for clause indicators
            if (line.startswith('Clause') or line.startswith('Section') or 
                line.startswith('Article') or line.startswith('Paragraph')):
                
                # Save previous clause
                if current_clause and current_clause.get('text'):
                    clauses.append(current_clause)
                
                # Start new clause
                current_clause = {
                    'clause_number': line,
                    'text': '',
                    'title': '',
                    'section_reference': line
                }
            
            elif current_clause is not None:
                # Add to current clause text
                if line.startswith('Title:') or line.startswith('Description:'):
                    current_clause['title'] = line.split(':', 1)[1].strip()
                elif line.startswith('Type:') or line.startswith('Category:'):
                    current_clause['preliminary_type'] = line.split(':', 1)[1].strip()
                else:
                    current_clause['text'] += ' ' + line
        
        # Add the last clause
        if current_clause and current_clause.get('text'):
            clauses.append(current_clause)
        
        # Clean up clause texts
        for clause in clauses:
            clause['text'] = clause['text'].strip()
        
        return clauses
    
    def _classify_clause_with_llm(self, clause_text: str) -> Dict[str, Any]:
        """Classify clause using LLM."""
        try:
            classification_prompt = f"""
            Classify the following contract clause into one of these categories:
            1. safety_compliance - Work health & safety, hazard management, safety procedures
            2. environmental_compliance - Environmental protection, rehabilitation, waste management
            3. operational_compliance - Mining operations, production requirements, reporting
            4. commercial_terms - Payment, delivery, warranties, pricing
            5. legal_provisions - Contract terms, dispute resolution, governing law
            
            Clause text: {clause_text[:1000]}
            
            Respond with JSON format:
            {{
                "primary_type": "category_name",
                "confidence": 0.8,
                "reasoning": "brief explanation",
                "has_mandatory_language": true/false,
                "key_requirements": ["requirement1", "requirement2"]
            }}
            """
            
            result = self.llm._call(classification_prompt)
            
            # Try to parse JSON response
            try:
                classification = json.loads(result)
                return classification
            except json.JSONDecodeError:
                # Fallback to simple parsing
                return self._parse_classification_text(result)
                
        except Exception as e:
            logger.error(f"LLM classification error: {e}")
            return {
                'primary_type': 'unknown',
                'confidence': 0.0,
                'reasoning': f'Classification failed: {str(e)}',
                'has_mandatory_language': False,
                'key_requirements': []
            }
    
    def _parse_classification_text(self, text: str) -> Dict[str, Any]:
        """Parse text-based classification response."""
        classification = {
            'primary_type': 'unknown',
            'confidence': 0.0,
            'reasoning': text[:200],
            'has_mandatory_language': False,
            'key_requirements': []
        }
        
        text_lower = text.lower()
        
        # Extract primary type
        categories = ['safety_compliance', 'environmental_compliance', 'operational_compliance', 
                     'commercial_terms', 'legal_provisions']
        
        for category in categories:
            if category.replace('_', ' ') in text_lower or category in text_lower:
                classification['primary_type'] = category
                classification['confidence'] = 0.7
                break
        
        # Check for mandatory language indicators
        mandatory_indicators = ['shall', 'must', 'required', 'mandatory', 'obligated']
        if any(indicator in text_lower for indicator in mandatory_indicators):
            classification['has_mandatory_language'] = True
        
        return classification
    
    def _fallback_clause_extraction(self, document_text: str) -> Dict[str, Any]:
        """Fallback clause extraction using pattern matching."""
        try:
            tool = ClauseExtractionTool()
            result = tool._run(document_text)
            parsed_result = json.loads(result)
            
            return {
                'clauses': parsed_result.get('clauses', []),
                'total_clauses': parsed_result.get('total_clauses', 0),
                'extraction_method': 'pattern_based_fallback',
                'processing_notes': 'Used pattern-based extraction as fallback'
            }
            
        except Exception as e:
            logger.error(f"Fallback extraction error: {e}")
            return {
                'clauses': [],
                'total_clauses': 0,
                'extraction_method': 'failed',
                'error': str(e)
            }
    
    def analyze_document_structure(self, document_text: str) -> Dict[str, Any]:
        """Analyze overall document structure using LLM."""
        try:
            structure_prompt = f"""
            Analyze the structure of this legal/contract document and provide insights:
            
            Document text (first 2000 characters):
            {document_text[:2000]}
            
            Please identify:
            1. Document type (contract, regulation, terms & conditions, etc.)
            2. Main sections or parts
            3. Compliance areas covered
            4. Key parties mentioned
            5. Jurisdiction (if mentioned)
            
            Respond in JSON format with your analysis.
            """
            
            result = self.llm._call(structure_prompt)
            
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                return {
                    'document_type': 'unknown',
                    'analysis': result[:500],
                    'error': 'Could not parse LLM response as JSON'
                }
                
        except Exception as e:
            logger.error(f"Document structure analysis error: {e}")
            return {
                'document_type': 'unknown',
                'error': str(e)
            }
