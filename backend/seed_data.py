from app import create_app, db
from app.models import Paper, Author, Keyword, Citation

def seed_database():
  """Add sample data to database"""
  app = create_app()

  with app.app_context():
    db.drop_all()
    db.create_all()


    author1 = Author(name='Atif')
    author2= Author(name='Glenn')
    author3 = Author(name='Sam Altman')

    keyword1 = Keyword(name='machine learning')
    keyword2 = Keyword(name='artificial intelligence')
    keyword3 =Keyword(name='neural networks')

    paper1 = Paper(
      title='Introduction to Machine Learning',
      abstract='A comprehensive overview of machine learning techniques.',
      year=2020,
      citation_count=150

    )
    paper1.authors.extend([author1, author2])
    paper1.keywords.extend([keyword1, keyword2])

    paper2 = Paper(
      title='Deep Neural Networks in AI',
      abstract='Exploring deep learning architectures for AI applications.',
      year=2021,
      citation_count=89
    )

    paper2.authors.append(author2)
    paper2.keywords.extend([keyword2, keyword3])

    paper3 = Paper(
      title='Advanced ML Algorithms',
      abstract='Recent advances in machine learning algorithms',
      year=2022,
      citation_count=45
    )
    paper3.authors.extend([author1,author3])
    paper3.keywords.append(keyword1)

    db.session.add_all([author1,author2,author3])
    db.session.add_all([keyword1,keyword2,keyword3])
    db.session.add_all([paper1,paper2,paper3])
    db.session.commit()

    citation1 = Citation(citing_paper_id=paper2.id, cited_paper_id=paper1.id)
    citation2 = Citation(citing_paper_id=paper3.id, cited_paper_id=paper1.id)

    db.session.add_all([citation1,citation2])
    db.session.commit()

    print('Sample data added successfully.')
    print(f'Papers: {Paper.query.count()}')
    print(f'Authors: {Author.query.count()}')
    print(f'Keywords: {Keyword.query.count()}')
    print(f'Citations: {Citation.query.count()}')

if __name__ == '__main__':
  seed_database()    

