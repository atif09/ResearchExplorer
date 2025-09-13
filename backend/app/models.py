from app import db
from datetime import datetime

paper_authors = db.Table('paper_authors',
                         db.Column('paper_id', db.Integer, db.ForeignKey('paper.id'), primary_key=True),
                         db.Column('author_id', db.Integer, db.ForeignKey('author.id'), primary_key=True)
                         )

paper_keywords = db.Table('paper_keywords',
                         db.Column('paper_id', db.Integer, db.ForeignKey('paper.id'), primary_key=True),
                         db.Column('keyword_id', db.Integer, db.ForeignKey('keyword.id'), primary_key=True))

class Paper(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False, index=True)
    abstract = db.Column(db.Text)
    year = db.Column(db.Integer, nullable=False, index=True)
    citation_count = db.Column(db.Integer, default=0, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    authors = db.relationship('Author', secondary=paper_authors, 
                             back_populates='papers', lazy='dynamic')
    keywords = db.relationship('Keyword', secondary=paper_keywords, 
                              back_populates='papers', lazy='dynamic')
    
    
    cited_papers = db.relationship('Citation', 
                                 foreign_keys='Citation.citing_paper_id', 
                                 backref='citing_paper',
                                 cascade='all, delete-orphan')
    citing_papers = db.relationship('Citation', 
                                  foreign_keys='Citation.cited_paper_id', 
                                  backref='cited_paper')
    

    __table_args__ = (
        db.Index('idx_paper_year_citations', 'year', 'citation_count'),
        db.Index('idx_paper_title', 'title'),
    )
    
    def __repr__(self):
        return f'<Paper {self.title[:50]}...>'
    
    def to_dict(self, include_relationships=True):
        base_dict = {
            'id': self.id,
            'title': self.title,
            'abstract': self.abstract,
            'year': self.year,
            'citation_count': self.citation_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_relationships:
            base_dict.update({
                'authors': [author.name for author in self.authors],
                'keywords': [keyword.name for keyword in self.keywords],
                'citation_network': {
                    'cites_count': len(self.cited_papers),
                    'cited_by_count': len(self.citing_papers)
                }
            })
        
        return base_dict
    
    def to_export_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'abstract': self.abstract,
            'year': self.year,
            'citation_count': self.citation_count,
            'authors': [{'id': a.id, 'name': a.name} for a in self.authors],
            'keywords': [{'id': k.id, 'name': k.name} for k in self.keywords],
            'citations': {
                'cites': [c.cited_paper_id for c in self.cited_papers],
                'cited_by': [c.citing_paper_id for c in self.citing_papers]
            },
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    papers = db.relationship('Paper', secondary=paper_authors, 
                           back_populates='authors', lazy='dynamic')
    
    def __repr__(self):
        return f'<Author {self.name}>'
    
    def to_dict(self, include_papers=False):
        base_dict = {
            'id': self.id,
            'name': self.name,
            'paper_count': self.papers.count(),
            'total_citations': sum(paper.citation_count for paper in self.papers),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_papers:
            base_dict['papers'] = [paper.to_dict(include_relationships=False) 
                                 for paper in self.papers]
        
        return base_dict
    
    def get_collaboration_network(self):
        collaborators = set()
        for paper in self.papers:
            for co_author in paper.authors:
                if co_author.id != self.id:
                    collaborators.add(co_author)
        return list(collaborators)
    
    def get_h_index(self):
        citation_counts = sorted([paper.citation_count for paper in self.papers], 
                                reverse=True)
        h_index = 0
        for i, citations in enumerate(citation_counts):
            if citations >= i + 1:
                h_index = i + 1
            else:
                break
        return h_index

class Keyword(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    papers = db.relationship('Paper', secondary=paper_keywords, 
                           back_populates='keywords', lazy='dynamic')
    
    def __repr__(self):
        return f'<Keyword {self.name}>'
    
    def to_dict(self, include_papers=False):
        base_dict = {
            'id': self.id,
            'name': self.name,
            'paper_count': self.papers.count(),
            'total_citations': sum(paper.citation_count for paper in self.papers),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_papers:
            base_dict['papers'] = [paper.to_dict(include_relationships=False) 
                                 for paper in self.papers]
        
        return base_dict
    
    def get_trending_score(self, years_back=5):
        current_year = datetime.now().year
        recent_papers = self.papers.filter(
            Paper.year >= current_year - years_back
        ).count()
        total_papers = self.papers.count()
        
        if total_papers == 0:
            return 0
        
        return (recent_papers / total_papers) * 100

class Citation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    citing_paper_id = db.Column(db.Integer, db.ForeignKey('paper.id'), nullable=False)
    cited_paper_id = db.Column(db.Integer, db.ForeignKey('paper.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    

    __table_args__ = (
        db.UniqueConstraint('citing_paper_id', 'cited_paper_id', name='unique_citation'),
        db.CheckConstraint('citing_paper_id != cited_paper_id', name='no_self_citation'),
        db.Index('idx_citation_citing', 'citing_paper_id'),
        db.Index('idx_citation_cited', 'cited_paper_id'),
    )
    
    def __repr__(self):
        return f'<Citation {self.citing_paper_id} -> {self.cited_paper_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'citing_paper_id': self.citing_paper_id,
            'cited_paper_id': self.cited_paper_id,
            'citing_paper_title': self.citing_paper.title if self.citing_paper else None,
            'cited_paper_title': self.cited_paper.title if self.cited_paper else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


def create_sample_data():

    try:
        # Check if sample data already exists
        if Paper.query.count() > 0:
            print("Sample data already exists. Skipping creation.")
            return
 
        authors_data = [
            "John Smith", "Jane Doe", "Michael Johnson", "Sarah Wilson", 
            "David Brown", "Emily Davis", "Robert Miller", "Lisa Anderson",
            "James Taylor", "Maria Garcia", "Christopher Lee", "Jennifer White"
        ]
        
        authors = []
        for author_name in authors_data:
            author = Author(name=author_name)
            db.session.add(author)
            authors.append(author)
   
        keywords_data = [
            "machine learning", "artificial intelligence", "data mining", 
            "neural networks", "deep learning", "computer vision", 
            "natural language processing", "robotics", "cloud computing",
            "cybersecurity", "blockchain", "quantum computing", "big data",
            "internet of things", "augmented reality", "virtual reality"
        ]
        
        keywords = []
        for keyword_name in keywords_data:
            keyword = Keyword(name=keyword_name.lower())
            db.session.add(keyword)
            keywords.append(keyword)

        papers_data = [
            {
                "title": "Deep Learning Approaches for Computer Vision Applications",
                "abstract": "This paper explores various deep learning architectures for computer vision tasks including image classification, object detection, and semantic segmentation.",
                "year": 2023,
                "citation_count": 45,
                "author_indices": [0, 1, 2],
                "keyword_indices": [0, 4, 5]
            },
            {
                "title": "Natural Language Processing in Healthcare: A Comprehensive Survey",
                "abstract": "A comprehensive review of NLP techniques applied to healthcare data, including electronic health records, clinical notes, and medical literature.",
                "year": 2022,
                "citation_count": 78,
                "author_indices": [2, 3, 4],
                "keyword_indices": [6, 0, 12]
            },
            {
                "title": "Blockchain Technology for Secure IoT Communications",
                "abstract": "This study presents a novel framework for securing Internet of Things communications using blockchain technology and smart contracts.",
                "year": 2023,
                "citation_count": 32,
                "author_indices": [4, 5],
                "keyword_indices": [10, 13, 9]
            },
            {
                "title": "Quantum Computing Applications in Machine Learning",
                "abstract": "An exploration of how quantum computing can accelerate machine learning algorithms and solve complex optimization problems.",
                "year": 2024,
                "citation_count": 15,
                "author_indices": [6, 7, 8],
                "keyword_indices": [11, 0, 1]
            },
            {
                "title": "Cloud-Based Big Data Analytics for Smart Cities",
                "abstract": "A framework for analyzing large-scale urban data using cloud computing resources to improve city planning and resource management.",
                "year": 2022,
                "citation_count": 56,
                "author_indices": [8, 9, 10],
                "keyword_indices": [8, 12, 13]
            },
            {
                "title": "Cybersecurity Challenges in Augmented Reality Systems",
                "abstract": "This paper identifies security vulnerabilities in AR systems and proposes mitigation strategies for protecting user data and privacy.",
                "year": 2023,
                "citation_count": 28,
                "author_indices": [10, 11, 0],
                "keyword_indices": [9, 14, 15]
            },
            {
                "title": "Robotics and AI Integration for Industrial Automation",
                "abstract": "A study on integrating artificial intelligence with robotic systems to improve manufacturing efficiency and quality control.",
                "year": 2022,
                "citation_count": 67,
                "author_indices": [1, 3, 5],
                "keyword_indices": [7, 1, 0]
            },
            {
                "title": "Data Mining Techniques for Social Media Analysis",
                "abstract": "An investigation of data mining methods for extracting insights from social media platforms and understanding user behavior patterns.",
                "year": 2021,
                "citation_count": 89,
                "author_indices": [7, 9, 11],
                "keyword_indices": [2, 12, 6]
            }
        ]
        
        papers = []
        for paper_data in papers_data:
            paper = Paper(
                title=paper_data["title"],
                abstract=paper_data["abstract"],
                year=paper_data["year"],
                citation_count=paper_data["citation_count"]
            )
       
            for author_idx in paper_data["author_indices"]:
                if author_idx < len(authors):
                    paper.authors.append(authors[author_idx])
       
            for keyword_idx in paper_data["keyword_indices"]:
                if keyword_idx < len(keywords):
                    paper.keywords.append(keywords[keyword_idx])
            
            db.session.add(paper)
            papers.append(paper)
    
        db.session.commit()

        citation_pairs = [
            (papers[0].id, papers[1].id), 
            (papers[0].id, papers[7].id),  
            (papers[1].id, papers[7].id),  
            (papers[2].id, papers[4].id),  
            (papers[3].id, papers[0].id),  
            (papers[4].id, papers[7].id),  
            (papers[5].id, papers[2].id),  
            (papers[6].id, papers[1].id),  
            (papers[6].id, papers[7].id),  
        ]
        
        for citing_id, cited_id in citation_pairs:
            citation = Citation(
                citing_paper_id=citing_id,
                cited_paper_id=cited_id
            )
            db.session.add(citation)
        
        db.session.commit()
        
        print(f"Sample data created successfully:")
        print(f"- {len(authors)} authors")
        print(f"- {len(keywords)} keywords") 
        print(f"- {len(papers)} papers")
        print(f"- {len(citation_pairs)} citations")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating sample data: {str(e)}")
        raise


def backup_database():
    try:
        from datetime import datetime

        papers = Paper.query.all()
        authors = Author.query.all()
        keywords = Keyword.query.all()
        citations = Citation.query.all()

        backup_data = {
            'backup_info': {
                'created_at': datetime.utcnow().isoformat(),
                'version': '1.0',
                'total_records': {
                    'papers': len(papers),
                    'authors': len(authors),
                    'keywords': len(keywords),
                    'citations': len(citations)
                }
            },
            'data': {
                'papers': [paper.to_export_dict() for paper in papers],
                'authors': [author.to_dict(include_papers=False) for author in authors],
                'keywords': [keyword.to_dict(include_papers=False) for keyword in keywords],
                'citations': [citation.to_dict() for citation in citations]
            }
        }

        import json
        import os

        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
 
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'research_explorer_backup_{timestamp}.json'
        backup_filepath = os.path.join(backup_dir, backup_filename)

        with open(backup_filepath, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        print(f"Database backup created successfully: {backup_filepath}")
        print(f"Backup contains:")
        print(f"- {len(papers)} papers")
        print(f"- {len(authors)} authors")
        print(f"- {len(keywords)} keywords")
        print(f"- {len(citations)} citations")
        
        return backup_filepath
        
    except Exception as e:
        print(f"Error creating database backup: {str(e)}")
        raise


def restore_database(backup_data):
    try:

        print("Clearing existing database data...")
        Citation.query.delete()

        db.session.execute(paper_authors.delete())
        db.session.execute(paper_keywords.delete())
        Paper.query.delete()
        Author.query.delete()
        Keyword.query.delete()
        db.session.commit()
 
        if isinstance(backup_data, str):
            import json
            backup_data = json.loads(backup_data)
 
        if 'data' not in backup_data:
            raise ValueError("Invalid backup data: missing 'data' key")
        
        data = backup_data['data']

        print("Restoring authors...")
        author_id_mapping = {}
        for author_data in data.get('authors', []):
            author = Author(name=author_data['name'])
            if 'created_at' in author_data and author_data['created_at']:
                author.created_at = datetime.fromisoformat(author_data['created_at'].replace('Z', '+00:00'))
            db.session.add(author)
            db.session.flush()  # Get the new ID
            author_id_mapping[author_data['id']] = author.id
  
        print("Restoring keywords...")
        keyword_id_mapping = {}
        for keyword_data in data.get('keywords', []):
            keyword = Keyword(name=keyword_data['name'])
            if 'created_at' in keyword_data and keyword_data['created_at']:
                keyword.created_at = datetime.fromisoformat(keyword_data['created_at'].replace('Z', '+00:00'))
            db.session.add(keyword)
            db.session.flush() 
            keyword_id_mapping[keyword_data['id']] = keyword.id
  
        print("Restoring papers...")
        paper_id_mapping = {}
        for paper_data in data.get('papers', []):
            paper = Paper(
                title=paper_data['title'],
                abstract=paper_data.get('abstract', ''),
                year=paper_data['year'],
                citation_count=paper_data.get('citation_count', 0)
            )
 
            if 'created_at' in paper_data and paper_data['created_at']:
                paper.created_at = datetime.fromisoformat(paper_data['created_at'].replace('Z', '+00:00'))
            if 'updated_at' in paper_data and paper_data['updated_at']:
                paper.updated_at = datetime.fromisoformat(paper_data['updated_at'].replace('Z', '+00:00'))
            
            db.session.add(paper)
            db.session.flush() 
            paper_id_mapping[paper_data['id']] = paper.id
   
            if 'authors' in paper_data:
                for author_data in paper_data['authors']:
                    if isinstance(author_data, dict) and 'id' in author_data:
                        old_author_id = author_data['id']
                        if old_author_id in author_id_mapping:
                            new_author_id = author_id_mapping[old_author_id]
                            author = Author.query.get(new_author_id)
                            if author:
                                paper.authors.append(author)
            
            if 'keywords' in paper_data:
                for keyword_data in paper_data['keywords']:
                    if isinstance(keyword_data, dict) and 'id' in keyword_data:
                        old_keyword_id = keyword_data['id']
                        if old_keyword_id in keyword_id_mapping:
                            new_keyword_id = keyword_id_mapping[old_keyword_id]
                            keyword = Keyword.query.get(new_keyword_id)
                            if keyword:
                                paper.keywords.append(keyword)
        
      
        db.session.commit()

        print("Restoring citations...")
        for citation_data in data.get('citations', []):
            old_citing_id = citation_data['citing_paper_id']
            old_cited_id = citation_data['cited_paper_id']
            
            if old_citing_id in paper_id_mapping and old_cited_id in paper_id_mapping:
                new_citing_id = paper_id_mapping[old_citing_id]
                new_cited_id = paper_id_mapping[old_cited_id]
                
                citation = Citation(
                    citing_paper_id=new_citing_id,
                    cited_paper_id=new_cited_id
                )
                
                if 'created_at' in citation_data and citation_data['created_at']:
                    citation.created_at = datetime.fromisoformat(citation_data['created_at'].replace('Z', '+00:00'))
                
                db.session.add(citation)
        
        db.session.commit()

        restored_counts = {
            'papers': Paper.query.count(),
            'authors': Author.query.count(),
            'keywords': Keyword.query.count(),
            'citations': Citation.query.count()
        }
        
        print("Database restored successfully!")
        print(f"Restored:")
        for entity, count in restored_counts.items():
            print(f"- {count} {entity}")
        
        return restored_counts
        
    except Exception as e:
        db.session.rollback()
        print(f"Error restoring database: {str(e)}")
        raise