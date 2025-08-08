import json
import asyncio
from typing import Dict, Any, Optional, Tuple
import openai
from anthropic import AsyncAnthropic
from ..models.resume_models import ParsedResume
from ..config import settings

class LLMParser:
    def __init__(self):
        if settings.OPENAI_API_KEY:
            self.openai_client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.openai_client = None
            
        if settings.ANTHROPIC_API_KEY:
            self.anthropic_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        else:
            self.anthropic_client = None
    
    async def parse(self, text: str, provider: str = "openai") -> Tuple[ParsedResume, float]:
        """Parse resume using LLM"""
        try:
            if provider == "openai" and self.openai_client:
                return await self._parse_with_openai(text)
            elif provider == "anthropic" and self.anthropic_client:
                return await self._parse_with_anthropic(text)
            else:
                raise ValueError(f"Provider {provider} not available or not configured")
                
        except Exception as e:
            raise Exception(f"LLM parsing failed: {str(e)}")
    
    async def _parse_with_openai(self, text: str) -> Tuple[ParsedResume, float]:
        """Parse using OpenAI GPT-4o-mini"""
        prompt = self._create_parsing_prompt(text)
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4000,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            parsed_resume = self._convert_to_pydantic(result)
            parsed_resume.parsing_method = "llm_openai"
            
            # Calculate confidence based on completeness
            confidence = self._calculate_llm_confidence(parsed_resume)
            parsed_resume.confidence_score = confidence
            
            return parsed_resume, confidence
            
        except Exception as e:
            raise Exception(f"OpenAI parsing error: {str(e)}")
    
    async def _parse_with_anthropic(self, text: str) -> Tuple[ParsedResume, float]:
        """Parse using Anthropic Claude"""
        prompt = self._create_parsing_prompt(text)
        
        try:
            response = await self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=4000,
                temperature=0.1,
                system=self._get_system_prompt(),
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract JSON from response
            content = response.content[0].text
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            json_content = content[json_start:json_end]
            
            result = json.loads(json_content)
            parsed_resume = self._convert_to_pydantic(result)
            parsed_resume.parsing_method = "llm_anthropic"
            
            confidence = self._calculate_llm_confidence(parsed_resume)
            parsed_resume.confidence_score = confidence
            
            return parsed_resume, confidence
            
        except Exception as e:
            raise Exception(f"Anthropic parsing error: {str(e)}")
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for LLM"""
        return """You are an expert resume parser. Extract information from resumes and return it in the specified JSON format.

Rules:
1. Extract only information that is explicitly present in the resume
2. Use null for missing information, don't make assumptions
3. For dates, preserve the original format when possible
4. For experience, separate each job into individual entries
5. Group skills by category when possible
6. Extract achievements and accomplishments from job descriptions
7. Return valid JSON only, no additional text

Return the data in this exact JSON structure:
{
  "personal_info": {
    "full_name": "string or null",
    "email": "string or null",
    "phone": "string or null",
    "address": "string or null",
    "linkedin": "string or null",
    "github": "string or null",
    "portfolio": "string or null"
  },
  "summary": "string or null",
  "experience": [
    {
      "company": "string or null",
      "position": "string or null",
      "start_date": "string or null",
      "end_date": "string or null",
      "is_current": "boolean",
      "description": "string or null",
      "achievements": ["array of strings"]
    }
  ],
  "education": [
    {
      "institution": "string or null",
      "degree": "string or null",
      "field_of_study": "string or null",
      "graduation_date": "string or null",
      "gpa": "string or null"
    }
  ],
  "skills": [
    {
      "category": "string or null",
      "skills": ["array of strings"]
    }
  ],
  "certifications": [
    {
      "name": "string or null",
      "issuer": "string or null",
      "date": "string or null",
      "credential_id": "string or null"
    }
  ],
  "projects": [
    {
      "name": "string or null",
      "description": "string or null",
      "technologies": ["array of strings"],
      "url": "string or null",
      "start_date": "string or null",
      "end_date": "string or null"
    }
  ],
  "languages": [
    {
      "language": "string or null",
      "proficiency": "string or null"
    }
  ]
}"""
    
    def _create_parsing_prompt(self, text: str) -> str:
        """Create parsing prompt with resume text"""
        return f"""Please parse the following resume text and extract all relevant information according to the JSON schema provided in the system prompt.

Resume Text:
{text}

Return only the JSON object, no additional text or explanation."""
    
    def _convert_to_pydantic(self, data: Dict[str, Any]) -> ParsedResume:
        """Convert parsed JSON to Pydantic model"""
        try:
            return ParsedResume.model_validate(data)
        except Exception as e:
            # Create a basic structure if validation fails
            return ParsedResume()
    
    def _calculate_llm_confidence(self, parsed_resume: ParsedResume) -> float:
        """Calculate confidence score for LLM parsed resume"""
        score = 0.0
        
        # Personal info
        if parsed_resume.personal_info.full_name:
            score += 0.2
        if parsed_resume.personal_info.email:
            score += 0.15
        if parsed_resume.personal_info.phone:
            score += 0.1
        
        # Main sections
        if parsed_resume.experience:
            score += 0.25
        if parsed_resume.education:
            score += 0.15
        if parsed_resume.skills:
            score += 0.1
        
        # Additional content
        if parsed_resume.summary:
            score += 0.05