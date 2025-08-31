import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from urllib.parse import urlparse
from .models import LinkItem, LinkCategory, TaskStatus

class LinkProcessor:
    """Process and categorize links from user messages."""
    
    def __init__(self):
        # URL patterns
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        
        # Deadline patterns
        self.deadline_patterns = [
            r'deadline[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'due[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4})',
            r'in\s+(\d+)\s+(?:day|days|week|weeks)',
        ]
        
        # Category keywords
        self.category_keywords = {
            LinkCategory.JOB_APPLICATION: [
                'job', 'position', 'career', 'employment', 'hire', 'recruit',
                'apply', 'application', 'resume', 'cv', 'interview'
            ],
            LinkCategory.GRANT_APPLICATION: [
                'grant', 'funding', 'scholarship', 'fellowship', 'award',
                'submission', 'proposal', 'fund', 'financial'
            ],
            LinkCategory.NOTES_TO_READ: [
                'read', 'article', 'paper', 'document', 'note', 'study',
                'research', 'analysis', 'report', 'blog', 'post'
            ],
            LinkCategory.RESEARCH: [
                'research', 'study', 'investigation', 'analysis', 'survey',
                'experiment', 'data', 'findings', 'methodology'
            ],
            LinkCategory.LEARNING: [
                'learn', 'course', 'tutorial', 'education', 'training',
                'workshop', 'seminar', 'lecture', 'class', 'lesson'
            ],
            LinkCategory.PERSONAL: [
                'personal', 'private', 'family', 'friend', 'social',
                'hobby', 'interest', 'entertainment'
            ]
        }
    
    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text."""
        return self.url_pattern.findall(text)
    
    def extract_deadline(self, text: str) -> Optional[datetime]:
        """Extract deadline from text."""
        text_lower = text.lower()
        
        # Check for "in X days/weeks" patterns
        in_pattern = re.search(r'in\s+(\d+)\s+(day|days|week|weeks)', text_lower)
        if in_pattern:
            number = int(in_pattern.group(1))
            unit = in_pattern.group(2)
            if unit.startswith('week'):
                return datetime.now() + timedelta(weeks=number)
            else:
                return datetime.now() + timedelta(days=number)
        
        # Check for date patterns
        for pattern in self.deadline_patterns:
            match = re.search(pattern, text_lower)
            if match:
                date_str = match.group(1)
                try:
                    # Try different date formats
                    for fmt in ['%m/%d/%Y', '%m-%d-%Y', '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d']:
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
                    
                    # Try month name format
                    month_pattern = r'(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{2,4})'
                    month_match = re.search(month_pattern, date_str)
                    if month_match:
                        day = int(month_match.group(1))
                        month_name = month_match.group(2)
                        year = int(month_match.group(3))
                        
                        month_map = {
                            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
                            'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
                            'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                        }
                        
                        if month_name in month_map:
                            return datetime(year, month_map[month_name], day)
                except:
                    continue
        
        return None
    
    def categorize_link(self, url: str, text: str = "") -> LinkCategory:
        """Categorize a link based on URL and context."""
        url_lower = url.lower()
        text_lower = text.lower()
        combined_text = f"{url_lower} {text_lower}"
        
        # Check domain-specific patterns
        domain = urlparse(url).netloc.lower()
        
        # Job sites
        job_domains = ['linkedin.com', 'indeed.com', 'glassdoor.com', 'monster.com', 'careerbuilder.com']
        if any(job_domain in domain for job_domain in job_domains):
            return LinkCategory.JOB_APPLICATION
        
        # Grant/funding sites
        grant_domains = ['grants.gov', 'foundationcenter.org', 'scholarships.com']
        if any(grant_domain in domain for grant_domain in grant_domains):
            return LinkCategory.GRANT_APPLICATION
        
        # Learning platforms
        learning_domains = ['coursera.org', 'edx.org', 'udemy.com', 'khanacademy.org', 'skillshare.com']
        if any(learning_domain in domain for learning_domain in learning_domains):
            return LinkCategory.LEARNING
        
        # Research/reading sites
        research_domains = ['arxiv.org', 'researchgate.net', 'scholar.google.com', 'pubmed.ncbi.nlm.nih.gov']
        if any(research_domain in domain for research_domain in research_domains):
            return LinkCategory.RESEARCH
        
        # Check keyword patterns
        for category, keywords in self.category_keywords.items():
            if any(keyword in combined_text for keyword in keywords):
                return category
        
        return LinkCategory.OTHER
    
    def extract_title(self, url: str, text: str = "") -> str:
        """Extract or generate a title for the link."""
        # If there's context in the text, try to extract a title
        if text.strip():
            # Look for text that might be a title (before or after the URL)
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if line and not self.url_pattern.search(line) and len(line) < 100:
                    return line[:50] + "..." if len(line) > 50 else line
        
        # Fallback to domain name
        domain = urlparse(url).netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        return f"Link from {domain}"
    
    def process_message(self, text: str) -> List[LinkItem]:
        """Process a message and extract link items."""
        urls = self.extract_urls(text)
        if not urls:
            return []
        
        deadline = self.extract_deadline(text)
        link_items = []
        
        for url in urls:
            category = self.categorize_link(url, text)
            title = self.extract_title(url, text)
            
            link_item = LinkItem(
                url=url,
                title=title,
                category=category,
                deadline=deadline,
                description=text[:200] + "..." if len(text) > 200 else text
            )
            
            link_items.append(link_item)
        
        return link_items
    
    def parse_status_update(self, text: str) -> Optional[Tuple[str, TaskStatus]]:
        """Parse status update commands like 'done 123' or 'mark 456 as done'."""
        text_lower = text.lower()
        
        # Patterns for status updates
        patterns = [
            r'(done|complete|finished)\s+(\w+)',
            r'mark\s+(\w+)\s+as\s+(done|complete|finished|todo|in_progress)',
            r'(\w+)\s+is\s+(done|complete|finished|todo|in_progress)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                if len(match.groups()) == 2:
                    link_id = match.group(1)
                    status_text = match.group(2)
                else:
                    link_id = match.group(2)
                    status_text = match.group(1)
                
                # Map status text to TaskStatus
                status_map = {
                    'done': TaskStatus.DONE,
                    'complete': TaskStatus.DONE,
                    'finished': TaskStatus.DONE,
                    'todo': TaskStatus.TODO,
                    'in_progress': TaskStatus.IN_PROGRESS,
                }
                
                if status_text in status_map:
                    return link_id, status_map[status_text]
        
        return None
