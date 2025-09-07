from flask import Blueprint, request, jsonify
from app import db
from app.models import Paper, Author, Keyword,Citation
from sqlalchemy.exc import IntegrityError

bp = Blueprint('main', __name__)

@bp.route('/papers', methods=['GET'])
def get_papers():
  """GET all papers with optional pagination"""
  page = request.args.get('page', 1, type=int)
  per_page = request.args.get('per_page', 20, type=int)

  papers = Paper.query.paginate(
    page=page, per_page=per_page, error_out=False
  )

  return jsonify({

    'papers': [paper.to_dict() for paper in papers.items],
    'total': papers.total,
    'pages': papers.pages,
    'current_page': page
  })

@bp.route('/papers/<int:paper_id>', methods=['GET'])
def get_paper(paper_id):
  """Get specific paper by ID"""
  paper = Paper.query.get_or_404(paper_id)
  return jsonify(paper.to_dict())

@bp.route('/papers', methods=['POST'])
def create_paper():
  """Create a new paper"""
  data = request.get_json() 

  if not data or 'title' not in data or 'year' not in data:
    return jsonify({'error': 'Title and year are required'}), 400
  
  try:
      
      paper = Paper(
          title=data['title'],
          abstract=data.get('abstract', ''),
          year=data['year'],
          citation_count=data.get('citation_count', 0)
      )

      for author_name in data.get('authors', []):
        author = Author.query.filter_by(name=author_name).first()
        if not author:
          author = Author(Name=author_name)
          db.session.add(author)
        paper.authors.append(author)

        db.session.add(paper)
        db.session.commit()

        return jsonify({
          'message': 'Paper created successfully',
          'paper': paper.to_dict()
        }), 201
      
  except Exception as e:
    db.session.rollback()
    return jsonify({'error': str(e)}), 500
  

@bp.route('/papers/<int:paper_id>', methods=['PUT'])
def update_paper(paper_id):
  """Update existing paper"""
  paper = Paper.query.get_or_404(paper_id)
  data = request.get_json()

  try:
    if 'title' in data:
      paper.title = data['title']
    if 'abstract' in data:
      paper.abstract = data['abstract']
    if 'year' in data:
      paper.year = data['year']
    if 'citation_count' in data:
      paper.citation_count = data['citation_count']

    db.session.commit()
    return jsonify({
      'message': 'Paper updated successfully',
      'paper': paper.to_dict()
    })
  
  except Exception as e:
    db.session.rollback()
    return jsonify({'error': str(e)}), 500
  

@bp.route('/papers/<int:paper_id>', methods=['DELETE'])
def delete_paper(paper_id):
  """Delete paper"""
  paper =Paper.query.get_or_404(paper_id)
  try:
    db.session.delete(paper)
    db.session.commit()
    return jsonify({'message': 'Paper deleted successfully'})
  except Exception as e:
    db.session.rollback()
    return jsonify({'error': str(e)}), 500
  

@bp.route('/authors', methods=['GET'])
def get_authors():
  """Get all authors"""
  authors = Author.query.all()
  return jsonify([author.to_dict() for author in authors])

@bp.route('/authors/<int:author_id>', methods=['GET'])
def get_author(author_id):
  """Get specific author with their papers"""
  author = Author.query.get_or_404(author_id)
  return jsonify({
    **author.to_dict(),
    'papers': [paper.to_dict() for paper in author.papers]
  })

@bp.route('/keywords', methods=['GET'])
def get_keywords():
  """Get all keywords"""
  keywords = Keyword.query.all()
  return jsonify([keyword.to_dict() for keyword in keywords])

@bp.route('/keywords/<int:keyword_Id>', methods=['GET'])
def get_keyword(keyword_id):
  """Get specific keyword with associated papers"""
  keyword = Keyword.query.get_or_404(keyword_id)
  return jsonify({
    **keyword.to_dict(),
    'papers': [paper.to_dict() for paper in keyword.papers]
  })

@bp.route('/citations', methods=['POST'])
def create_citation():
  """Create citation relationship between papers"""
  data = request.get_json()

  if not data or 'citing_paper_id' not in data or 'cited_paper_id' not in data:
    return jsonify({'error': 'citing_paper_id and cited_paper_id are required'}), 400
  
  try:
    citation = Citation(
      citing_paper_id=data['citing_paper_id'],
      cited_paper_id=data['cited_paper_id']
    )

    db.session.add(citation)
    db.session.commit()

    return jsonify({
      'message': 'Citation created successfully',
      'citation': citation.to_dict()
    }), 201
  
  except IntegrityError:
    db.session.rollback()
    return jsonify({'error': 'Invalid citation (duplicate or self-citation)'}), 400
  except Exception as e:
    db.session.rollback()
    return jsonify({'error': str(e)}), 500
  

@bp.route('/citations', methods=['GET'])
def get_citations():
  """Get all citations"""
  citations = Citation.query.all()
  return jsonify([citation.to_dict() for citation in citations])

@bp.route('/search', methods=['GET'])
def search_papers():
  """Search papers by title, author, or keyword"""
  query = request.args.get('q', '').strip()
  year_from = request.args.get('year_from', type=int)
  year_to = request.args.get('year_to', type = int)

  papers = Paper.query

  if query:
    papers = papers.filter(Paper.title.contains(query))

  if year_from:
    papers = papers.filter(Paper.year >= year_from)

  if year_to:
    papers = papers.filter(Paper.year <= year_to)

  results = papers.all()

  return jsonify({
    'papers': [paper.to_dict() for paper in results],
    'count': len(results)
  })

@bp.route('/health', methods=['GET'])
def health_check():
  """API health check"""
  return jsonify({
    'status':'healthy',
    'message': 'ResearchExplorer API is running'
  })