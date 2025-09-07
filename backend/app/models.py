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
    title = db.Column(db.String(500), nullable=False)
    abstract = db.Column(db.Text)
    year = db.Column(db.Integer, nullable=False)
    citation_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    
    authors = db.relationship('Author', secondary=paper_authors, backref=db.backref('papers', lazy='dynamic'))
    keywords = db.relationship('Keyword', secondary=paper_keywords, backref=db.backref('papers', lazy='dynamic'))
    
    
    cited_papers = db.relationship('Citation', 
                                 foreign_keys='Citation.citing_paper_id', 
                                 backref='citing_paper',
                                 cascade='all, delete-orphan')
    citing_papers = db.relationship('Citation', 
                                  foreign_keys='Citation.cited_paper_id', 
                                  backref='cited_paper')
    
    def __repr__(self):
        return f'<Paper {self.title}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'abstract': self.abstract,
            'year': self.year,
            'citation_count': self.citation_count,
            'authors': [author.name for author in self.authors],
            'keywords': [keyword.name for keyword in self.keywords],
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Author(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Author {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'paper_count': self.papers.count()
        }

class Keyword(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Keyword {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'paper_count': self.papers.count()
        }

class Citation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    citing_paper_id = db.Column(db.Integer, db.ForeignKey('paper.id'), nullable=False)
    cited_paper_id = db.Column(db.Integer, db.ForeignKey('paper.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    
    __table_args__ = (
        db.UniqueConstraint('citing_paper_id', 'cited_paper_id', name='unique_citation'),
        db.CheckConstraint('citing_paper_id != cited_paper_id', name='no_self_citation')
    )
    
    def __repr__(self):
        return f'<Citation {self.citing_paper_id} -> {self.cited_paper_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'citing_paper_id': self.citing_paper_id,
            'cited_paper_id': self.cited_paper_id,
            'citing_paper_title': self.citing_paper.title if self.citing_paper else None,
            'cited_paper_title': self.cited_paper.title if self.cited_paper else None
        }