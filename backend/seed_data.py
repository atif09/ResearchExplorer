from app import create_app, db
from app.models import Paper, Author, Keyword, Citation
import random

def seed_database():
    """Add comprehensive sample data for testing all features"""
    app = create_app()
    
    with app.app_context():
        
        db.drop_all()
        db.create_all()
        
   
        authors_data = [
            "John Smith", "Jane Doe", "Bob Johnson", "Alice Chen", "David Wilson",
            "Sarah Garcia", "Michael Brown", "Lisa Wang", "Robert Davis", "Emily Rodriguez",
            "James Taylor", "Anna Patel", "Thomas Anderson", "Maria Lopez", "Kevin Zhang",
            "Rachel Green", "Daniel Kim", "Jessica Lee", "Mark Williams", "Laura Martinez"
        ]
        authors = []
        for name in authors_data:
            author = Author(name=name)
            authors.append(author)
            db.session.add(author) 

        keywords_data = [
          "machine learning", "artificial intelligence", "neural networks", "deep learning",
          "computer vision", "natural language processing", "robotics", "data mining",
          "big data", "cloud computing", "blockchain", "cybersecurity", "quantum computing",
          "bioinformatics", "medical imaging", "genomics", "climate modeling", "renewable energy",
          "sustainable technology", "human-computer interaction", "augmented reality", "virtual reality",
          "edge computing", "internet of things", "distributed systems", "microservices"
        ]
        keywords = []
        for name in keywords_data:
            
            keyword = Keyword(name=name.lower())
            keywords.append(keyword)
            db.session.add(keyword)    

        
        papers_data = [
            {
                'title': 'Introduction to Machine Learning Algorithms',
                'abstract': 'A comprehensive overview of fundamental machine learning techniques including supervised and unsupervised learning methods.',
                'year': 2018,
                'citation_count': 245,
                'author_indices': [0, 1, 4],
                'keyword_indices': [0, 1, 7]
            },
            {
                'title': 'Deep Neural Networks for Computer Vision',
                'abstract': 'Exploring convolutional neural networks and their applications in image recognition and computer vision tasks.',
                'year': 2019,
                'citation_count': 189,
                'author_indices': [1, 5, 8],
                'keyword_indices': [2, 3, 4]
            },
            {
                'title': 'Natural Language Processing with Transformers',
                'abstract': 'Advanced techniques in NLP using transformer architectures for language understanding and generation.',
                'year': 2020,
                'citation_count': 156,
                'author_indices': [2, 6, 9],
                'keyword_indices': [5, 1, 3]
            },
            {
                'title': 'Blockchain Technology in Healthcare',
                'abstract': 'Applications of distributed ledger technology for secure medical data management and patient privacy.',
                'year': 2021,
                'citation_count': 78,
                'author_indices': [3, 7, 10],
                'keyword_indices': [10, 12, 14]
            },
            {
                'title': 'Quantum Computing Algorithms',
                'abstract': 'Fundamental quantum algorithms and their potential applications in cryptography and optimization.',
                'year': 2020,
                'citation_count': 134,
                'author_indices': [4, 11, 15],
                'keyword_indices': [12, 1]
            },
            {
                'title': 'Big Data Analytics for Climate Modeling',
                'abstract': 'Large-scale data processing techniques applied to climate prediction and environmental monitoring.',
                'year': 2022,
                'citation_count': 92,
                'author_indices': [5, 12, 16],
                'keyword_indices': [8, 16, 17]
            },
            {
                'title': 'Robotics and Autonomous Systems',
                'abstract': 'Integration of AI and robotics for autonomous navigation and decision-making in complex environments.',
                'year': 2021,
                'citation_count': 67,
                'author_indices': [6, 13, 17],
                'keyword_indices': [6, 1, 0]
            },
            {
                'title': 'Cybersecurity in IoT Networks',
                'abstract': 'Security challenges and solutions for Internet of Things devices and network infrastructure.',
                'year': 2023,
                'citation_count': 34,
                'author_indices': [7, 14, 18],
                'keyword_indices': [11, 23, 24]
            },
            {
                'title': 'Medical Image Analysis using Deep Learning',
                'abstract': 'Application of convolutional neural networks for medical diagnosis and treatment planning.',
                'year': 2022,
                'citation_count': 156,
                'author_indices': [8, 1, 19],
                'keyword_indices': [14, 3, 4]
            },
            {
                'title': 'Edge Computing for Real-time Applications',
                'abstract': 'Distributed computing architectures for low-latency processing at network edges.',
                'year': 2023,
                'citation_count': 45,
                'author_indices': [9, 15, 0],
                'keyword_indices': [22, 24, 9]
            },
            {
                'title': 'Sustainable Energy Systems with AI',
                'abstract': 'Machine learning approaches for optimizing renewable energy generation and distribution.',
                'year': 2023,
                'citation_count': 28,
                'author_indices': [10, 16, 2],
                'keyword_indices': [17, 0, 1]
            },
            {
                'title': 'Virtual Reality in Education',
                'abstract': 'Immersive technologies for enhanced learning experiences and remote education delivery.',
                'year': 2022,
                'citation_count': 73,
                'author_indices': [11, 17, 3],
                'keyword_indices': [21, 19, 1]
            },
            {
                'title': 'Genomics Data Processing at Scale',
                'abstract': 'High-performance computing solutions for large-scale genomic sequence analysis and variant detection.',
                'year': 2021,
                'citation_count': 98,
                'author_indices': [12, 18, 4],
                'keyword_indices': [15, 8, 13]
            },
            {
                'title': 'Human-Computer Interaction in AR Systems',
                'abstract': 'User interface design and interaction paradigms for augmented reality applications.',
                'year': 2023,
                'citation_count': 19,
                'author_indices': [13, 19, 5],
                'keyword_indices': [19, 20, 1]
            },
            {
                'title': 'Distributed Machine Learning Systems',
                'abstract': 'Scalable ML frameworks for training large models across distributed computing clusters.',
                'year': 2021,
                'citation_count': 112,
                'author_indices': [14, 0, 6],
                'keyword_indices': [0, 24, 25]
            },
            {
                'title': 'Advanced Computer Vision Techniques',
                'abstract': 'State-of-the-art methods in object detection, segmentation, and scene understanding.',
                'year': 2020,
                'citation_count': 178,
                'author_indices': [15, 1, 7],
                'keyword_indices': [4, 2, 3]
            },
            {
                'title': 'Microservices Architecture Patterns',
                'abstract': 'Design patterns and best practices for building scalable microservices-based applications.',
                'year': 2022,
                'citation_count': 87,
                'author_indices': [16, 2, 8],
                'keyword_indices': [25, 9, 24]
            },
            {
                'title': 'Bioinformatics and Precision Medicine',
                'abstract': 'Computational approaches for personalized treatment based on genetic and clinical data.',
                'year': 2021,
                'citation_count': 143,
                'author_indices': [17, 3, 9],
                'keyword_indices': [13, 15, 0]
            },
            {
                'title': 'Cloud-Native Application Development',
                'abstract': 'Modern development practices for building applications optimized for cloud environments.',
                'year': 2023,
                'citation_count': 52,
                'author_indices': [18, 4, 10],
                'keyword_indices': [9, 25, 24]
            },
            {
                'title': 'AI Ethics and Algorithmic Fairness',
                'abstract': 'Addressing bias and fairness concerns in machine learning systems and AI decision-making.',
                'year': 2022,
                'citation_count': 167,
                'author_indices': [19, 5, 11],
                'keyword_indices': [1, 0]
            }
        ]
        
        papers = []
        for paper_data in papers_data:
            paper = Paper(
                title=paper_data['title'],
                abstract=paper_data['abstract'],
                year=paper_data['year'],
                citation_count=paper_data['citation_count']
            )
            
   
            for author_idx in paper_data['author_indices']:
                paper.authors.append(authors[author_idx])
            
      
            for keyword_idx in paper_data['keyword_indices']:
                if keyword_idx < len(keywords):
                    paper.keywords.append(keywords[keyword_idx])
            
            papers.append(paper)
            db.session.add(paper)
        
        db.session.commit()
        
       
        citation_relationships = [
          
            (1, 0), (2, 0), (8, 0), (14, 0), (19, 0),
        
            (8, 1), (15, 1), (2, 1),
          
            (15, 1), (8, 15),
        
            (2, 1), (2, 0),
   
            (14, 5), (16, 14), (18, 14),
       
            (17, 12), (8, 17), (3, 17),
         
            (19, 0), (19, 1), (19, 2), (19, 14),
        
            (7, 3), (10, 5), (13, 11), (18, 16),
          
            (6, 0), (11, 13), (4, 0), (10, 14)
        ]
        
        citations = []
        unique_pairs = set()
        for citing_idx, cited_idx in citation_relationships:
            pair = (papers[citing_idx].id, papers[cited_idx].id)
            if pair not in unique_pairs and citing_idx != cited_idx:
                citation = Citation(
                    citing_paper_id=pair[0],
                    cited_paper_id=pair[1]
                )
                citations.append(citation)
                db.session.add(citation)
                unique_pairs.add(pair)

        try:
            db.session.commit()
        
        
            print("Comprehensive sample data added successfully!")
            print(f"Papers: {Paper.query.count()}")
            print(f"Authors: {Author.query.count()}")
            print(f"Keywords: {Keyword.query.count()}")
            print(f"Citations: {Citation.query.count()}")
        
 
            print("\n Database Statistics:")
            print(f"   • Average citations per paper: {db.session.query(db.func.avg(Paper.citation_count)).scalar():.1f}")
            print(f"   • Most cited paper: {Paper.query.order_by(Paper.citation_count.desc()).first().citation_count} citations")
            print(f"   • Year range: {Paper.query.with_entities(db.func.min(Paper.year)).scalar()} - {Paper.query.with_entities(db.func.max(Paper.year)).scalar()}")
            print(f"   • Most productive author: {max(authors, key=lambda a: a.papers.count()).name} ({max(authors, key=lambda a: a.papers.count()).papers.count()} papers)")
        except Exception as e: 
          db.session.rollback()
          print(f'Error adding citations: {e}')
if __name__ == '__main__':
    seed_database()
    

