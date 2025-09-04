"""
AI-powered document analysis module.
Provides intelligent document processing, text extraction, summarization, and insights.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import requests
from PIL import Image
import PyPDF2
from io import BytesIO

@dataclass
class AnalysisResult:
    """Result of AI document analysis."""
    document_id: str
    analysis_type: str
    text_content: str
    summary: str
    key_points: List[str]
    sentiment: str
    language: str
    word_count: int
    page_count: int
    confidence: float
    insights: Dict[str, Any]
    created_at: datetime

class AIAnalysisManager:
    """Manages AI-powered document analysis using OpenAI and other AI services."""
    
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.azure_endpoint = os.getenv('AZURE_COGNITIVE_ENDPOINT')
        self.azure_key = os.getenv('AZURE_COGNITIVE_KEY')
        self.enabled = bool(self.openai_api_key or (self.azure_endpoint and self.azure_key))
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        if not self.enabled:
            self.logger.warning("AI analysis disabled - no API keys configured")
    
    def extract_text_from_pdf(self, file_path: str) -> tuple[str, int]:
        """Extract text content from PDF file."""
        try:
            text_content = ""
            page_count = 0
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)
                
                for page in pdf_reader.pages:
                    text_content += page.extract_text() + "\n"
            
            return text_content.strip(), page_count
        except Exception as e:
            self.logger.error(f"Error extracting text from PDF: {str(e)}")
            return "", 0
    
    def analyze_with_openai(self, text: str, analysis_type: str = "comprehensive") -> Dict[str, Any]:
        """Analyze text using OpenAI GPT."""
        if not self.openai_api_key:
            return {"error": "OpenAI API key not configured"}
        
        try:
            prompt = self._build_analysis_prompt(text, analysis_type)
            
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "You are an expert document analyst. Provide detailed, structured analysis."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 1500
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                return self._parse_ai_response(content)
            else:
                self.logger.error(f"OpenAI API error: {response.status_code}")
                return {"error": f"OpenAI API error: {response.status_code}"}
                
        except Exception as e:
            self.logger.error(f"Error analyzing with OpenAI: {str(e)}")
            return {"error": str(e)}
    
    def _build_analysis_prompt(self, text: str, analysis_type: str) -> str:
        """Build analysis prompt based on type."""
        base_prompt = f"""
        Analyze the following document text and provide a structured response in JSON format:

        Document Text:
        {text[:3000]}...

        Please provide analysis in this exact JSON structure:
        {{
            "summary": "Brief summary of the document (2-3 sentences)",
            "key_points": ["point1", "point2", "point3"],
            "sentiment": "positive/negative/neutral",
            "language": "detected language",
            "document_type": "type of document",
            "topics": ["topic1", "topic2"],
            "insights": {{
                "complexity": "low/medium/high",
                "readability": "easy/moderate/difficult",
                "urgency": "low/medium/high",
                "action_items": ["action1", "action2"]
            }}
        }}
        """
        
        if analysis_type == "legal":
            base_prompt += "\nFocus on legal terminology, clauses, and obligations."
        elif analysis_type == "financial":
            base_prompt += "\nFocus on financial terms, numbers, and monetary implications."
        elif analysis_type == "technical":
            base_prompt += "\nFocus on technical specifications, procedures, and requirements."
        
        return base_prompt
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response and extract structured data."""
        try:
            # Try to extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Fallback parsing
                return {
                    "summary": response[:200] + "...",
                    "key_points": ["Analysis completed"],
                    "sentiment": "neutral",
                    "language": "unknown",
                    "document_type": "unknown",
                    "topics": ["general"],
                    "insights": {
                        "complexity": "medium",
                        "readability": "moderate",
                        "urgency": "low",
                        "action_items": []
                    }
                }
        except json.JSONDecodeError:
            self.logger.error("Failed to parse AI response as JSON")
            return {"error": "Failed to parse AI response"}
    
    def analyze_document(self, file_path: str, file_type: str = "pdf", analysis_type: str = "comprehensive") -> AnalysisResult:
        """Perform comprehensive AI analysis on a document."""
        if not self.enabled:
            raise ValueError("AI analysis is disabled - configure API keys")
        
        try:
            # Extract text based on file type
            if file_type.lower() == "pdf":
                text_content, page_count = self.extract_text_from_pdf(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
            
            if not text_content:
                raise ValueError("No text content found in document")
            
            # Perform AI analysis
            ai_result = self.analyze_with_openai(text_content, analysis_type)
            
            if "error" in ai_result:
                raise ValueError(f"AI analysis failed: {ai_result['error']}")
            
            # Create analysis result
            document_id = os.path.basename(file_path)
            word_count = len(text_content.split())
            
            return AnalysisResult(
                document_id=document_id,
                analysis_type=analysis_type,
                text_content=text_content[:1000] + "..." if len(text_content) > 1000 else text_content,
                summary=ai_result.get("summary", ""),
                key_points=ai_result.get("key_points", []),
                sentiment=ai_result.get("sentiment", "neutral"),
                language=ai_result.get("language", "unknown"),
                word_count=word_count,
                page_count=page_count,
                confidence=0.85,  # Default confidence
                insights=ai_result.get("insights", {}),
                created_at=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing document: {str(e)}")
            raise
    
    def get_document_insights(self, text: str) -> Dict[str, Any]:
        """Get quick insights about document content."""
        word_count = len(text.split())
        char_count = len(text)
        
        # Basic text analysis
        sentences = text.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        readability = "easy" if avg_sentence_length < 15 else "moderate" if avg_sentence_length < 25 else "difficult"
        
        return {
            "word_count": word_count,
            "character_count": char_count,
            "sentence_count": len(sentences),
            "avg_sentence_length": round(avg_sentence_length, 2),
            "readability": readability,
            "estimated_reading_time": round(word_count / 200, 1)  # Average reading speed
        }
    
    def classify_document_type(self, text: str) -> str:
        """Classify document type based on content."""
        text_lower = text.lower()
        
        # Simple keyword-based classification
        if any(word in text_lower for word in ["contract", "agreement", "terms", "conditions"]):
            return "legal"
        elif any(word in text_lower for word in ["invoice", "payment", "cost", "price", "budget"]):
            return "financial"
        elif any(word in text_lower for word in ["specification", "technical", "system", "protocol"]):
            return "technical"
        elif any(word in text_lower for word in ["report", "analysis", "findings", "conclusion"]):
            return "report"
        else:
            return "general"

# Global AI analysis manager instance
ai_analysis_manager = AIAnalysisManager()