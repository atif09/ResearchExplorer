from flask import Blueprint, request, jsonify
from app import db
from app.models import Paper, Author, Keyword,Citation
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func,desc,asc
import json

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
          author = Author(name=author_name)
          db.session.add(author)
        paper.authors.append(author)

      for keyword_name in data.get('keywords', []):
            keyword = Keyword.query.filter_by(name=keyword_name.lower()).first()
            if not keyword:
                keyword = Keyword(name=keyword_name.lower())
                db.session.add(keyword)
            paper.keywords.append(keyword)

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
  author=request.args.get('author', '').strip()
  keyword = request.args.get('keyword', '').strip()
  min_citations = request.args.get('min_citations', type=int)
  max_citations = request.args.get('max_citations', type=int)
  query = request.args.get('q', '').strip()
  year_from = request.args.get('year_from', type=int)
  year_to = request.args.get('year_to', type = int)

  papers = Paper.query
  if author:
    papers = papers.join(Paper.authors).filter(Author.name.contains(author))

  if keyword:
    papers = papers.join(Paper.keywords).filter(Keyword.name.contains(keyword))

  if query:
    papers = papers.filter(Paper.title.contains(query))

  if year_from:
    papers = papers.filter(Paper.year >= year_from)

  if year_to:
    papers = papers.filter(Paper.year <= year_to)

  if min_citations is not None:
    papers = papers.filter(Paper.citation_count >= min_citations)
  if max_citations is not None:
    papers = papers.filter(Paper.citation_count <= max_citations)

  results = papers.distinct().all()

  return jsonify({
    'papers': [paper.to_dict() for paper in results],
    'count': len(results),
    'filters_applied': {
      'query': query,
      'author': author,
      'keyword': keyword,
      'year_from': year_from,
      'year_to': year_to,
      'min_citations': min_citations,
      'max_citations': max_citations
    }
  })

@bp.route('/graph/data', methods=['GET'])
def get_graph_data():
  year_from = request.args.get('year_from', type=int)
  year_to=request.args.get('year_to', type=int)
  keyword=request.args.get('keyword', '').strip()
  max_nodes=request.args.get('max_nodes', 100, type=int)

  papers_query = Paper.query

  if year_from:
    papers_query= papers_query.filter(Paper.year >= year_from)
  if year_to:
    papers_query = papers_query.filter(Paper.year <= year_to)

  if keyword:
    papers_query = papers_query.join(Paper.keywords).filter(Keyword.name.contains(keyword.lower()))

  papers = papers_query.order_by(desc(Paper.citation_count)).limit(max_nodes).all()
  paper_ids = [p.id for p in papers]

  nodes=[]
  for paper in papers:
    nodes.append({
      'id': paper.id,
      'title': paper.title,
      'year': paper.year,
      'citation_count': paper.citation_count,
      'authors': [author.name for author in paper.authors],
      'keywords': [keyword.name for keyword in paper.keywords],
      'type': 'paper'
    })
  
  citations=Citation.query.filter(
    Citation.citing_paper_id.in_(paper_ids),
    Citation.cited_paper_id.in_(paper_ids)
  ).all()

  edges=[]
  for citation in citations:
    edges.append({
      'source': citation.citing_paper_id,
      'target': citation.cited_paper_id,
      'type': 'citation'
    })
  
  return jsonify({
    'nodes': nodes,
    'edges': edges,
    'stats': {
      'total_nodes': len(nodes),
      'total_edges': len(edges),
      'filters_applied': {
        'year_from': year_from,
        'year_to': year_to,
        'keyword': keyword,
        'max_nodes': max_nodes
      }
    }
  })

@bp.route('/graph/subgraph/<int:paper_id>', methods=['GET'])
def get_subgraph(paper_id):
  depth=request.args.get('depth',1,type=int)

  center_paper = Paper.query.get_or_404(paper_id)

  paper_ids = {paper_id}
  nodes = [center_paper]

  for _ in range(depth): 
    citing_papers = Paper.query.join(Citation, Citation.citing_paper_id==Paper.id)\
      .filter(Citation.cited_paper_id.in_(paper_ids)).all()
    
    cited_papers = Paper.query.join(Citation, Citation.cited_paper_id == Paper.id)\
      .filter(Citation.citing_paper_id.in_(paper_ids)).all()
    
    new_papers = citing_papers + cited_papers
    for paper in new_papers:
      if paper.id not in paper_ids:
        paper_ids.add(paper.id)
        nodes.append(paper)

  node_data = []
  for paper in nodes:
    node_data.append({
      'id': paper.id,
      'title': paper.title,
      'year': paper.year,
      'citation_count': paper.citation_count,
      'authors': [author.name for author in paper.authors],
      'keywords': [keyword.name for keyword in paper.keywords],
      'is_center': paper.id == paper_id,
      'type': 'paper'
    })

  citations = Citation.query.filter(
    Citation.citing_paper_id.in_(paper_ids),
    Citation.cited_paper_id.in_(paper_ids)
  ).all()

  edges = []
  for citation in citations:
    edges.append({
      'source': citation.citing_paper_id,
      'target': citation.cited_paper_id,
      'type': 'citation'
    })
  
  return jsonify({
    'center_paper_id': paper_id,
    'nodes': node_data,
    'edges': edges,
    'stats': {
      'total_nodes': len(node_data),
      'total_edges': len(edges),
      'depth': depth
    }
  })

@bp.route('/trends/papers-per-year', methods=['GET'])
def papers_per_year():
  keyword = request.args.get('keyword', '').strip()
  author = request.args.get('authopr', '').strip()

  query = db.session.query(Paper.year, func.count(Paper.id).label('count'))

  if keyword:
    query=query.join(Paper.keywords).filter(Keyword.name.contains(keyword.lower()))
  if author:
    query = query.join(Paper.authors).filter(Author.name.contains(author))
  
  results = query.group_by(Paper.year).order_by(Paper.year).all()

  return jsonify({
    'data': [{'year': year, 'count': count} for year, count in results],
    'filters': {'keyword': keyword, 'author': author}
  })

@bp.route('/trends/keywords-over-time', methods=['GET'])
def keywords_over_time():
  limit=request.args.get('limit', 10, type=int)

  top_keywords = db.session.query(Keyword.name, func.count(Paper.id).label('total_papers'))\
    .join(Keyword.papers)\
    .group_by(Keyword.name)\
    .order_by(desc('total_papers'))\
    .limit(limit).all()
  
  keyword_trends={}
  for keyword_name, _ in top_keywords:

    yearly_counts = db.session.query(Paper.year, func.count(Paper.id).label('count'))\
      .join(Paper.keywords)\
      .filter(Keyword.name==keyword_name)\
      .group_by(Paper.year)\
      .order_by(Paper.year).all()
    
    keyword_trends[keyword_name] = [
      {'year': year, 'count': count} for year, count in yearly_counts
    ]
  
  return jsonify({
    'trends': keyword_trends,
    'top_keywords': [name for name, _ in top_keywords]
  })

@bp.route('/trends/citation-analysis', methods=['GET'])
def citation_analysis():

  most_cited = Paper.query.order_by(desc(Paper.citation_count)).limit(10).all()

  citation_by_year = db.session.query(
    Paper.year,
    func.avg(Paper.citation_count).label('avg_citations'),
    func.sum(Paper.citation_count).label('total_citations'),
    func.count(Paper.id).label('paper_count')
  ).group_by(Paper.year).order_by(Paper.year).all()

  return jsonify({
    'most_cited_papers': [paper.to_dict() for paper in most_cited],
    'citation_trends': [
      {
        'year': year,
        'avg_citations': float(avg_citations or 0),
        'total_citations': total_citations or 0,
        'paper_count': paper_count
      }
      for year, avg_citations, total_citations, paper_count in citation_by_year
    
    ]
  })

@bp.route('/export/papers', methods=['GET'])
def export_papers():
  format_type = request.args.get('format', 'json').lower()

  query=request.args.get('q', '').strip()
  year_from=request.args.get('year_from', type=int)
  year_to = request.args.get('year_to', type=int)

  papers_query = Paper.query

  if query:
    papers_query = papers_query.filter(Paper.title.contains(query))
  if year_from:
    papers_query= papers_query.filter(Paper.year >= year_from)
  if year_to:
    papers_query = papers_query.filter(Paper.year <= year_to)

  papers = papers_query.all()

  if format_type == 'json': 
    return jsonify({
      'papers': [paper.to_dict() for paper in papers],
      'export_info': {
        'total_papers': len(papers),
        'exported_at': func.now(),
        'filters_applied': {
          'query': query,
          'year_from': year_from,
          'year_to': year_to
        }
      }
    })
  else:
    return jsonify({'error': 'Only JSON format supported currently'}), 400
  

@bp.route('/export/graph-data', methods=['POST'])
def export_graph_data():
  data=request.get_json()

  if not data or 'node_ids' not in data:
    return jsonify({'error': 'node_ids required'}), 400
  
  node_ids = data['node_ids']
  papers=Paper.query.filter(Paper.id.in_(node_ids)).all()

  citations = Citation.query.filter(
    Citation.citing_paper_id.in_(node_ids),
    Citation.cited_paper_id.in_(node_ids)
  ).all()

  return jsonify({
    'exported_subgraph': {
      'nodes': [paper.to_dict() for paper in papers],
      'edges': [citation.to_dict() for citation in citations]
    },

    'export_info': {
      'node_count': len(papers),
      'edge_count': len(citations),
      'exported_at': func.now()
    }
  })
  
@bp.route('/health', methods=['GET'])
def health_check():
  """API health check"""
  return jsonify({
    'status':'healthy',
    'message': 'ResearchExplorer API is running',
    'endpoints': {
      'papers': '/api/papers', 
      'search': '/api/search',
      'graph_data': '/api/graph/data',
      'trends': '/api/trends/*',
      'export': '/api/export/*'
    }
  })