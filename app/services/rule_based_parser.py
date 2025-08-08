import re
import spacy
from typing import Dict, List, Optional, Tuple
from ..models.resume_models import (
    ParsedResume, PersonalInfo, Experience, Education, 
    Skill, Certification, Project, Language
)

class RuleBasedParser:
    def __init__(self):
        # Load spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Fallback if model not installed
            self.nlp = None
        
        # Regex patterns
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}')
        self.linkedin_pattern = re.compile(r'linkedin\.com/in/[\w-]+', re.IGNORECASE)
        self.github_pattern = re.compile(r'github\.com/[\w-]+', re.IGNORECASE)
        self.url_pattern = re.compile(r'https?://[^\s]+')
        
        # Section keywords
        self.section_keywords = {
            'experience': ['experience', 'work experience', 'employment', 'work history', 'professional experience'],
            'education': ['education', 'academic background', 'qualifications', 'degrees'],
            'skills': ['skills', 'technical skills', 'competencies', 'expertise', 'technologies'],
            'certifications': ['certifications', 'certificates', 'licenses', 'credentials'],
            'projects': ['projects', 'personal projects', 'portfolio', 'work samples'],
            'summary': ['summary', 'objective', 'profile', 'about me', 'overview'],
            'languages': ['languages', 'language skills', 'linguistic skills']
        }
    
    def parse(self, text: str) -> Tuple[ParsedResume, float]:
        """Parse resume using rule-based approach"""
        sections = self._split_into_sections(text)
        
        parsed_resume = ParsedResume(
            personal_info=self._extract_personal_info(text, sections),
            summary=self._extract_summary(sections),
            experience=self._extract_experience(sections),
            education=self._extract_education(sections),
            skills=self._extract_skills(sections),
            certifications=self._extract_certifications(sections),
            projects=self._extract_projects(sections),
            languages=self._extract_languages(sections),
            parsing_method="rule_based"
        )
        
        confidence = self._calculate_confidence(parsed_resume, text)
        parsed_resume.confidence_score = confidence
        
        return parsed_resume, confidence
    
    def _split_into_sections(self, text: str) -> Dict[str, str]:
        """Split resume text into sections"""
        sections = {}
        lines = text.split('\n')
        current_section = 'header'
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line is a section header
            section_found = None
            for section, keywords in self.section_keywords.items():
                for keyword in keywords:
                    if keyword.lower() in line.lower() and len(line) < 50:
                        section_found = section
                        break
                if section_found:
                    break
            
            if section_found:
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                
                # Start new section
                current_section = section_found
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def _extract_personal_info(self, text: str, sections: Dict[str, str]) -> PersonalInfo:
        """Extract personal information"""
        header_text = sections.get('header', '')
        full_text = header_text + '\n' + text[:500]  # First 500 chars
        
        # Extract email
        email_matches = self.email_pattern.findall(full_text)
        email = email_matches[0] if email_matches else None
        
        # Extract phone
        phone_matches = self.phone_pattern.findall(full_text)
        phone = phone_matches[0] if phone_matches else None
        if isinstance(phone, tuple):
            phone = ''.join(phone)
        
        # Extract LinkedIn
        linkedin_matches = self.linkedin_pattern.findall(full_text)
        linkedin = f"https://{linkedin_matches[0]}" if linkedin_matches else None
        
        # Extract GitHub
        github_matches = self.github_pattern.findall(full_text)
        github = f"https://{github_matches[0]}" if github_matches else None
        
        # Extract name (first non-empty line that's not contact info)
        name = None
        for line in full_text.split('\n'):
            line = line.strip()
            if line and not any(pattern.search(line) for pattern in [
                self.email_pattern, self.phone_pattern, self.linkedin_pattern, self.github_pattern
            ]):
                if len(line) < 100 and not line.lower().startswith(('resume', 'cv', 'curriculum')):
                    name = line
                    break
        
        return PersonalInfo(
            full_name=name,
            email=email,
            phone=phone,
            linkedin=linkedin,
            github=github
        )
    
    def _extract_summary(self, sections: Dict[str, str]) -> Optional[str]:
        """Extract summary/objective"""
        summary_text = sections.get('summary', '')
        if summary_text:
            return summary_text.strip()
        return None
    
    def _extract_experience(self, sections: Dict[str, str]) -> List[Experience]:
        """Extract work experience"""
        experience_text = sections.get('experience', '')
        if not experience_text:
            return []
        
        experiences = []
        # Simple parsing - split by job entries (lines starting with company/position)
        entries = re.split(r'\n(?=[A-Z][^a-z\n]*[A-Z])', experience_text)
        
        for entry in entries:
            if not entry.strip():
                continue
                
            lines = [line.strip() for line in entry.split('\n') if line.strip()]
            if len(lines) < 2:
                continue
            
            # First line usually contains company and/or position
            first_line = lines[0]
            
            # Extract dates
            date_pattern = r'(\d{4}|\d{1,2}/\d{4}|\w+\s+\d{4})'
            dates = re.findall(date_pattern, entry)
            
            start_date = dates[0] if len(dates) > 0 else None
            end_date = dates[1] if len(dates) > 1 else None
            is_current = 'present' in entry.lower() or 'current' in entry.lower()
            
            # Simple heuristic to separate company and position
            company = None
            position = None
            
            if '|' in first_line:
                parts = first_line.split('|')
                company = parts[0].strip()
                position = parts[1].strip()
            elif ',' in first_line:
                parts = first_line.split(',')
                position = parts[0].strip()
                company = parts[1].strip()
            else:
                position = first_line
            
            description = '\n'.join(lines[1:]) if len(lines) > 1 else ''
            
            experiences.append(Experience(
                company=company,
                position=position,
                start_date=start_date,
                end_date=end_date,
                is_current=is_current,
                description=description
            ))
        
        return experiences
    
    def _extract_education(self, sections: Dict[str, str]) -> List[Education]:
        """Extract education information"""
        education_text = sections.get('education', '')
        if not education_text:
            return []
        
        educations = []
        entries = education_text.split('\n\n')
        
        for entry in entries:
            if not entry.strip():
                continue
            
            lines = [line.strip() for line in entry.split('\n') if line.strip()]
            
            # Extract graduation date
            date_pattern = r'(\d{4})'
            dates = re.findall(date_pattern, entry)
            graduation_date = dates[-1] if dates else None
            
            # Simple parsing
            institution = None
            degree = None
            field_of_study = None
            
            for line in lines:
                if any(keyword in line.lower() for keyword in ['university', 'college', 'institute', 'school']):
                    institution = line
                elif any(keyword in line.lower() for keyword in ['bachelor', 'master', 'phd', 'degree', 'bs', 'ms', 'ba', 'ma']):
                    if 'in' in line.lower():
                        parts = line.lower().split('in')
                        degree = parts[0].strip()
                        field_of_study = parts[1].strip() if len(parts) > 1 else None
                    else:
                        degree = line
            
            educations.append(Education(
                institution=institution,
                degree=degree,
                field_of_study=field_of_study,
                graduation_date=graduation_date
            ))
        
        return educations
    
    def _extract_skills(self, sections: Dict[str, str]) -> List[Skill]:
        """Extract skills"""
        skills_text = sections.get('skills', '')
        if not skills_text:
            return []
        
        # Simple extraction - split by common separators
        skills_raw = re.split(r'[,;•\n]', skills_text)
        skills_cleaned = [skill.strip() for skill in skills_raw if skill.strip()]
        
        # Group skills (simple approach)
        return [Skill(category="Technical Skills", skills=skills_cleaned)]
    
    def _extract_certifications(self, sections: Dict[str, str]) -> List[Certification]:
        """Extract certifications"""
        cert_text = sections.get('certifications', '')
        if not cert_text:
            return []
        
        certifications = []
        lines = [line.strip() for line in cert_text.split('\n') if line.strip()]
        
        for line in lines:
            # Extract date
            date_pattern = r'(\d{4}|\d{1,2}/\d{4})'
            dates = re.findall(date_pattern, line)
            date = dates[0] if dates else None
            
            # Remove date from name
            name = re.sub(r'\d{4}|\d{1,2}/\d{4}', '', line).strip()
            
            certifications.append(Certification(
                name=name,
                date=date
            ))
        
        return certifications
    
    def _extract_projects(self, sections: Dict[str, str]) -> List[Project]:
        """Extract projects"""
        projects_text = sections.get('projects', '')
        if not projects_text:
            return []
        
        projects = []
        entries = projects_text.split('\n\n')
        
        for entry in entries:
            if not entry.strip():
                continue
            
            lines = [line.strip() for line in entry.split('\n') if line.strip()]
            name = lines[0] if lines else None
            description = '\n'.join(lines[1:]) if len(lines) > 1 else ''
            
            # Extract technologies (simple pattern)
            tech_pattern = r'Technologies?:?\s*([^\n]+)'
            tech_match = re.search(tech_pattern, description, re.IGNORECASE)
            technologies = []
            if tech_match:
                technologies = [tech.strip() for tech in tech_match.group(1).split(',')]
            
            projects.append(Project(
                name=name,
                description=description,
                technologies=technologies
            ))
        
        return projects
    
    def _extract_languages(self, sections: Dict[str, str]) -> List[Language]:
        """Extract languages"""
        lang_text = sections.get('languages', '')
        if not lang_text:
            return []
        
        languages = []
        lines = [line.strip() for line in lang_text.split('\n') if line.strip()]
        
        for line in lines:
            # Simple parsing - language and proficiency
            if ':' in line or '(' in line:
                if ':' in line:
                    parts = line.split(':')
                    language = parts[0].strip()
                    proficiency = parts[1].strip() if len(parts) > 1 else None
                else:  # parentheses
                    parts = re.split(r'[()]', line)
                    language = parts[0].strip()
                    proficiency = parts[1].strip() if len(parts) > 1 else None
                
                languages.append(Language(
                    language=language,
                    proficiency=proficiency
                ))
            else:
                languages.append(Language(language=line))
        
        return languages
    
    def _calculate_confidence(self, parsed_resume: ParsedResume, original_text: str) -> float:
        """Calculate confidence score based on extracted information"""
        score = 0.0
        max_score = 100.0
        
        # Personal info scoring
        if parsed_resume.personal_info.full_name:
            score += 15
        if parsed_resume.personal_info.email:
            score += 15
        if parsed_resume.personal_info.phone:
            score += 10
        
        # Content scoring
        if parsed_resume.experience:
            score += 20
        if parsed_resume.education:
            score += 15
        if parsed_resume.skills:
            score += 15
        
        # Additional sections
        if parsed_resume.summary:
            score += 5
        if parsed_resume.certifications:
            score += 2.5
        if parsed_resume.projects:
            score += 2.5
        
        return min(score / max_score, 1.0)