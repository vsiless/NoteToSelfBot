import re
import requests
from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Dict, Any
from urllib.parse import urlparse
from .models import LinkItem, LinkCategory, TaskStatus
from bs4 import BeautifulSoup
import time

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
            r'apply\s+by\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'application\s+deadline[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'closes\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'ends\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
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
                    
                    # Try month name format (month first)
                    month_pattern1 = r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{1,2})(?:st|nd|rd|th)?\s+(\d{2,4})'
                    month_match1 = re.search(month_pattern1, date_str)
                    if month_match1:
                        month_name = month_match1.group(1)
                        day = int(month_match1.group(2))
                        year = int(month_match1.group(3))
                        
                        month_map = {
                            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
                            'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
                            'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                        }
                        
                        if month_name in month_map:
                            return datetime(year, month_map[month_name], day)
                    
                    # Try month name format (day first)
                    month_pattern2 = r'(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{2,4})'
                    month_match2 = re.search(month_pattern2, date_str)
                    if month_match2:
                        day = int(month_match2.group(1))
                        month_name = month_match2.group(2)
                        year = int(month_match2.group(3))
                        
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
    
    def fetch_webpage_content(self, url: str) -> Optional[Dict[str, Any]]:
        """Fetch and parse webpage content."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = ""
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            
            # Extract meta description
            description = ""
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc:
                description = meta_desc.get('content', '').strip()
            
            # Extract main content (focus on article, main, or body)
            content = ""
            main_content = soup.find(['article', 'main', '[role="main"]']) or soup.find('body')
            if main_content:
                # Remove script and style elements
                for script in main_content(["script", "style"]):
                    script.decompose()
                content = main_content.get_text(separator=' ', strip=True)
            
            return {
                'title': title,
                'description': description,
                'content': content,
                'url': url
            }
            
        except Exception as e:
            print(f"Error fetching webpage {url}: {e}")
            return None
    
    def extract_deadline_from_content(self, content: str) -> Optional[datetime]:
        """Extract deadline from webpage content."""
        if not content:
            return None
        
        content_lower = content.lower()
        
        # Enhanced deadline patterns for webpage content
        deadline_patterns = [
            r'apply\s+by\s+((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}(?:st|nd|rd|th)?\s+\d{2,4})',
            r'apply\s+by\s+(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4})',
            r'deadline[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'due[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'apply\s+by\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'application\s+deadline[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'closes\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'ends\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{2,4})',
        ]
        
        for pattern in deadline_patterns:
            match = re.search(pattern, content_lower)
            if match:
                date_str = match.group(1)
                try:
                    # Try different date formats
                    for fmt in ['%m/%d/%Y', '%m-%d-%Y', '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d']:
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
                    
                    # Try month name format (month first)
                    month_pattern1 = r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{1,2})(?:st|nd|rd|th)?\s+(\d{2,4})'
                    month_match1 = re.search(month_pattern1, date_str)
                    if month_match1:
                        month_name = month_match1.group(1)
                        day = int(month_match1.group(2))
                        year = int(month_match1.group(3))
                        
                        month_map = {
                            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
                            'may': 5, 'jun': 6, 'jul': 7, 'aug': 8,
                            'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
                        }
                        
                        if month_name in month_map:
                            return datetime(year, month_map[month_name], day)
                    
                    # Try month name format (day first)
                    month_pattern2 = r'(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{2,4})'
                    month_match2 = re.search(month_pattern2, date_str)
                    if month_match2:
                        day = int(month_match2.group(1))
                        month_name = month_match2.group(2)
                        year = int(month_match2.group(3))
                        
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
    
    def extract_title_from_content(self, content: Dict[str, Any]) -> str:
        """Extract title from webpage content."""
        if content.get('title'):
            return content['title']
        return "No title found"
    
    def extract_description_from_content(self, content: Dict[str, Any]) -> str:
        """Extract description from webpage content."""
        if content.get('description'):
            return content['description']
        
        # Fallback to first 200 characters of main content
        if content.get('content'):
            return content['content'][:200] + "..." if len(content['content']) > 200 else content['content']
        
        return "No description available"
    
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
        
        # Extract deadline from message text first
        message_deadline = self.extract_deadline(text)
        link_items = []
        
        for url in urls:
            print(f"🔍 Fetching content from: {url}")
            
            # Fetch webpage content
            webpage_content = self.fetch_webpage_content(url)
            
            # Extract information from webpage
            if webpage_content:
                # Extract deadline from webpage content
                webpage_deadline = self.extract_deadline_from_content(webpage_content['content'])
                deadline = webpage_deadline or message_deadline
                
                # Extract title and description from webpage
                title = self.extract_title_from_content(webpage_content)
                description = self.extract_description_from_content(webpage_content)
                
                print(f"📄 Found title: {title}")
                if deadline:
                    print(f"⏰ Found deadline: {deadline.strftime('%Y-%m-%d')}")
            else:
                # Fallback to message-based extraction
                deadline = message_deadline
                title = self.extract_title(url, text)
                description = text[:200] + "..." if len(text) > 200 else text
                print(f"⚠️ Could not fetch webpage, using fallback extraction")
            
            category = self.categorize_link(url, text)
            
            link_item = LinkItem(
                url=url,
                title=title,
                category=category,
                deadline=deadline,
                description=description
            )
            
            link_items.append(link_item)
            
            # Small delay to be respectful to servers
            time.sleep(1)
        
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
