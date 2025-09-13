from flask import Blueprint, request, jsonify, current_app
from app import db, cache
from app.models import Paper, Author, Keyword, Citation
from app.analytics import ResearchAnalytics
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, desc, asc
import json 
import csv
import io

bp = Blueprint('main', __name__)

@bp.route('/papers', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
def get_papers():
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
@cache.cached(timeout=300)
def get_paper(paper_id):
  paper = Paper.query.get_or_404(paper_id)
  return jsonify(paper.to_dict())

@bp.route('/papers/', methods=['POST'])
def create_paper():
  data = request.get_json()

  if not data or 'title' not in data or 'year' not in data:
    return jsonify({'error': 'Title and year are required'}),400
  
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
    return jsonify({'error': str(e)}),500


@bp.route('/papers/<int:paper_id>', methods=['PUT'])
def update_paper(paper_id):
  paper = Paper.query.get_or_404(paper_id)
  data = request.get_json()

  try: 
    if 'title' in data:
      paper.title = data ['title']

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
    return jsonify({'error': str(e)}),500
  
@bp.route('/papers/<int:paper_id>', methods=['DELETE'])
def delete_paper(paper_id):
  paper = Paper.query.get_or_404(paper_id)
  try:
    db.session.delete(paper)
    db.session.commit()
    return jsonify({'message': 'Paper deleted successfully'})
  
  except Exception as e:
    db.session.rollback()
    return jsonify({'error': str(e)}), 500
  
@bp.route('/papers/bulk', methods=['POST'])
def bulk_create_papers():
  data = request.get_json()

  if not data or 'papers' not in data:
    return jsonify({'error': 'Papers array required'}), 400
  
  created_papers = []
  errors = []

  for i, paper_data in enumerate(data['papers']):
    try: 
      paper = Paper(
        title=paper_data['title'],
        abstract=paper_data.get('abstract', ''),
        year=paper_data['year'],
        citation_count=paper_data.get('citation_count', 0)
      )

      for author_name in paper_data.get('authors', []):
        author = Author.query.filter_by(name=author_name).first()
        if not author:
          author = Author(name=author_name)
          db.session.add(author)

        paper.authors.append(author)

      for keyword_name in paper_data.get('keywords', []):
        keyword = Keyword.query.filter_by(name=keyword_name.lower()).first()
        if not keyword:
          keyword = Keyword(name=keyword_name.lower())
          db.session.add(keyword)
        paper.keywords.append(keyword)

      db.session.add(paper)
      created_papers.append(paper)

    except Exception as e:
      errors.append(f'Paper {i}: {str(e)}')

  try:
    db.session.commit()
    return jsonify({
      'message': f'Successfully created {len(created_papers)} papers',
      'created_count': len(created_papers),
      'errors': errors
    }), 201
  except Exception as e:
    db.session.rollback()
    return jsonify({'error': str(e)}), 500
  
@bp.route('/authors', methods=['GET'])
@cache.cached(timeout=300)
def get_authors():
  authors = Author.query.all()
  return jsonify([author.to_dict() for author in authors])

@bp.route('authors/<int:author_id>', methods=['GET'])
@cache.cached(timeout=300)
def get_author(author_id):
  author = Author.query.get_or_404(author_id)
  return jsonify({
    **author.to_dict(),
    'papers': [paper.to_dict() for paper in author.papers]
  })

@bp.route('/keywords', methods=['GET'])
@cache.cached(timeout=300)
def get_keywords():
  keywords = Keyword.query.all()
  return jsonify([keyword.to_dict() for keyword in keywords])

@bp.route('/keywords/<int:keyword_id>', methods=['GET'])
@cache.cached(timeout=300)
def get_keyword(keyword_id):
  keyword = Keyword.query.get_or_404(keyword_id)
  return jsonify({
    **keyword.to_dict(),
    'papers': [paper.to_dict() for paper in keyword.papers]
  })

@bp.route('/citations', methods=['POST'])
def create_citation():
  data = request.get_json()

  if not data or 'citing_paper_id' not in data or 'cited_paper_id' not in data:
    return jsonify({'error': 'citing_paper_id and cited_paper_id are required'}),400
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
    return jsonify({'error': 'Invalid citation (duplicate or self-citation)'}),400
  except Exception as e:
    db.session.rollback()
    return jsonify({'error': str(e)}), 500
  
@bp.route('/citations', methods=['GET'])
@cache.cached(timeout=300)
def get_citations():
  citations = Citation.query.all()
  return jsonify([citation.to_dict() for citation in citations])

@bp.route('/search', methods=['GET'])
def search_papers():
  author = request.args.get('author', '').strip()
  keyword = request.args.get('keyword', '').strip()
  min_citations = request.args.get('min_citations', type=int)
  max_citations = request.args.get('max_citations', type=int)
  query = request.args.get('q','').strip()
  year_from = request.args.get('year_from', type=int)
  year_to = request.args.get('year_to', type=int)

  papers = Paper.query

  if author:
    papers= papers.join(Paper.authors).filter(Author.name.contains(author))
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

@bp.route('/search/advanced', methods=['POST'])
def advanced_search():
  data = request.get_json()
  papers = Paper.query

  if data.get('text'):
    papers = papers.filter(Paper.title.contains(data['text']))

  if data.get('authors'):
    papers = papers.join(Paper.authors).filter(Author.name.in_(data['authors']))

  if data.get('keywords'):
    papers = papers.join(Paper.keywords).filter(Keyword.name.in_(data['keywords']))

  if data.get('citation_range'):
    min_cit = data['citation_range'].get('min')
    max_cit = data['citation_range'].get('max')
    if min_cit is not None:
      papers = papers.filter(Paper.citation_count >= min_cit)
    if max_cit is not None:
      papers = papers.filter(Paper.citation_count <= max_cit)

  if data.get('year_range'):
    min_year = data['year_range'].get('min')
    max_year = data['year_range'].get('max')
    if min_year is not None:
      papers = papers.filter(Paper.year >= min_year)
    if max_year is not None:
      papers = papers.filter(Paper.year <= max_year) 

  sort_by = data.get('sort_by', 'year')
  sort_order = data.get('sort_order', 'desc')

  if sort_by == 'citations': 
    papers = papers.order_by(desc(Paper.citation_count) if sort_order == 'desc' else asc(Paper.citation_count))
  elif sort_by == 'title':
    papers = papers.order_by(desc(Paper.title) if sort_order == 'desc' else asc(Paper.title))
  else: 
    papers = papers.order_by(desc(Paper.year) if sort_order == 'desc' else asc(Paper.year))
  
  results = papers.distinct().all()

  return jsonify({
    'papers': [paper.to_dict() for paper in results],
    'count': len(results)
  })

@bp.route('/suggestions/keywords', methods=['GET'])
@cache.cached(timeout=600, query_string=True)
def keyword_suggestions():
  query = request.args.get('q', '').strip()
  limit = request.args.get('limit', 10, type=int)

  if query:
    keywords = Keyword.query.filter(Keyword.name.contains(query.lower())).limit(limit).all()
  else:
    keywords = Keyword.query.order_by(desc(Keyword.id)).limit(limit).all()

  return jsonify([kw.name for kw in keywords])

@bp.route('/suggestions/authors', methods=['GET'])
@cache.cached(timeout=600, query_string=True)
def author_suggestions():
  query = request.args.get('q', '').strip()
  limit = request.args.get('limit', 10, type=int)

  if query:
    authors = Author.query.filter(Author.name.contains(query)).limit(limit).all()
  else:
    authors = Author.query.order_by(desc(Author.id)).limit(limit).all()

  return jsonify([author.name for author in authors])

@bp.route('/suggestions/similar-papers', methods=['POST'])
def suggest_similar_papers():
  data = request.get_json()

  if not data or 'title' not in data:
    return jsonify({'error': 'Title required'}), 400
  
  title = data['title']
  limit = data.get('limit', 5)

  papers = Paper.query.filter(Paper.title.contains(''.join(title.split()[:3]))).limit(limit).all()

  return jsonify({paper.to_dict() for paper in papers})

@bp.route('/graph/data', methods=['GET'])
@cache.cached(timeout=300, query_string=True)
def get_graph_data():
  year_from = request.args.get('year_from', type=int)
  year_to = request.args.get('year_to', type=int)
  keyword = request.args.get('keyword', '').strip()
  max_nodes = request.args.get('max_nodes', 100, type=int)

  papers_query = Paper.query

  if year_from:
    papers_query = papers_query.filter(Paper.year >= year_from)
  
  if year_to:
    papers_query = papers_query.filter(Paper.year <= year_to)
  
  if keyword:
    papers_query = papers_query.join(Paper.keywords).filter(Keyword.name.contains(keyword.lower()))

  papers = papers_query.order_by(desc(Paper.citation_count)).limit(max_nodes).all()
  paper_ids = [p.id for p in papers]

  nodes = []
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
@cache.cached(timeout=300, query_string=True)
def get_subgraph(paper_id):
  depth = request.args.get('depth', 1, type=int)

  center_paper = Paper.query.get_or_404(paper_id)

  paper_ids = {paper_id}
  nodes = [center_paper]

  for _ in range(depth):
    citing_papers = Paper.query.join(Citation, Citation.cited_paper_id == Paper.id)\
      .filter(Citation.cited_paper_id.in_(paper_ids)).all()
    
    cited_papers = Paper.query.join(Citation, Citation.cited_paper_id == Paper.id)\
      .filter(Citation.citing_paper_id.in_(paper_ids)).all()

    new_papers = citing_papers + cited_papers
    for paper in new_papers: 
      if paper.id not in paper_ids:
        paper_ids.add(paper.id)
        nodes.append(paper)

  node_data=[]
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

@bp.route('/analytics/research-hotspots', methods=['GET'])
@cache.cached(timeout=600, query_string=True)
def get_research_hotspots():
  year_from = request.args.get('year_from', type=int)
  year_to = request.args.get('year_to', type=int)
  limit = request.args.get('limit', 10, type=int)

  year_range = None
  if year_from and year_to:
    year_range = (year_from, year_to)

  hotspots = ResearchAnalytics.get_research_hotspots(year_range,limit)
  return jsonify({'research_hotspots': hotspots})

@bp.route('/analytics/collaboration-network', methods=['GET'])
@cache.cached(timeout=600, query_string=True)
def get_collaboration_network():
  min_papers = request.args.get('min_papers', 2, type=int)
  network = ResearchAnalytics.get_author_collaboration_network(min_papers)
  return jsonify(network)

@bp.route('/analytics/citation-patterns', methods=['GET'])
@cache.cached(timeout=600)
def get_citation_patterns():
  patterns = ResearchAnalytics.analyze_citation_patterns()
  return jsonify(patterns)

@bp.route('/analytics/keyword-evolution/<keyword>', methods=['GET'])
@cache.cached(timeout=600, query_string=True)
def get_keyword_evolution(keyword):
  years_back = request.args.get('years_back', 10, type=int)
  evolution = ResearchAnalytics.get_temporal_keyword_evolution(keyword, years_back)
  return jsonify(evolution)

@bp.route('/analytics/research-gaps', methods=['GET'])
@cache.cached(timeout=600, query_string=True)
def get_research_gaps():
  min_citations = request.args.get('min_citations', 50, type=int)
  max_recent = request.args.get('max_recent_papers', 5, type=int)
  gaps = ResearchAnalytics.identify_research_gaps(min_citations, max_recent)
  return jsonify({'research_gaps': gaps})

@bp.route('/trends/papers-per-year', methods=['GET'])
@cache.cached(timeout=600, query_string=True)
def papers_per_year():
  keyword = request.args.get('keyword', '').strip()
  author = request.args.get('author', '').strip()

  query = db.session.query(Paper.year, func.count(Paper.id).label('count'))

  if keyword:
    query = query.join(Paper.keywords).filter(Keyword.name.contains(keyword.lower()))

  if author:
    query = query.join(Paper.authors).filter(Author.name.contains(author))

  results = query.group_by(Paper.year).order_by(Paper.year).all()

  return jsonify({
    'data': [{'year': year, 'count': count} for year, count in results],
    'filters': {'keyword': keyword, 'author': author}
  })

@bp.route('/trends/keywords-over-time', methods=['GET'])
@cache.cached(timeout=600, query_string=True)
def keywords_over_time():
  limit = request.args.get('limit', 10, type=int)

  top_keywords = db.session.query(Keyword.name, func.count(Paper.id).label('total_papers'))\
    .join(Keyword.papers)\
    .group_by(Keyword.name)\
    .order_by(desc('total_papers'))\
    .limit(limit).all()
  
  keyword_trends = {}
  for keyword_name, _ in top_keywords:
    yearly_counts = db.session.query(Paper.year, func.count(Paper.id).label('count'))\
      .join(Paper.keywords)\
      .filter(Keyword.name == keyword_name)\
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
@cache.cached(timeout=600)
def citation_analysis():
  most_cited = Paper.query.order_by(desc(Paper.citation_count)).limit(10).all()

  citation_by_year = db.session.query(
    Paper.year,
    func.avg(Paper.citation_count).label('avg_citation'),
    func.sum(Paper.citation_count).label('total_citations'),
    func.count(Paper.id).label('paper_count')
  ).group_by(Paper.year).order_by(Paper.year).all()

  return jsonify({
    'most-cited_papers': [paper.to_dict() for paper in most_cited],
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
  query = request.args.get('q','').strip()
  year_from = request.args.get('year_from', type=int)
  year_to = request.args.get('year_to', type=int)

  papers_query = Paper.query

  if query:
    papers_query = papers_query.filter(Paper.title.contains(query))
  if year_from: 
    papers_query = papers_query.filter(Paper.year >= year_from)
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
  elif format_type == 'csv':
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['ID', 'Title', 'Abstract', 'Year', 'Citation Count', 'Authors', 'Keywords' ])

    for paper in papers:
      writer.writerow([
        paper.id,
        paper.title,
        paper.abstract,
        paper.year,
        paper.citation_count,
        '; '.join([author.name for author in paper.authors]),
        '; '.join([keyword.name for keyword in paper.keywords])
      ])
    
    return output.getvalue(), 200, {
      'Content-type': 'text/csv',
      'Content-Disposition': 'attachment; filename=papers.csv'
    }
  else:
    return jsonify({'error': 'Unsupported format. Use json or csv'}), 400
  
@bp.route('/export/graph-data', methods=['POST'])
def export_graph_data():
  data = request.get_json()

  if not data or 'node_ids' not in data:
    return jsonify({'error': 'node_ids required'}), 400

  node_ids = data['node_ids']
  papers = Paper.query.filter(Paper.id.in_(node_ids)).all()

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

@bp.route('/export/trends', methods=['GET'])
def export_trends():
    trends = {}

    yearly_counts = db.session.query(Paper.year, func.count(Paper.id).label('count'))\
        .group_by(Paper.year).order_by(Paper.year).all()
    trends['papers_per_year'] = [{'year': year, 'count': count} for year, count in yearly_counts]

    top_keywords = db.session.query(Keyword.name, func.count(Paper.id).label('count'))\
        .join(Keyword.papers)\
        .group_by(Keyword.name)\
        .order_by(desc('count'))\
        .limit(20).all()
    trends['top_keywords'] = [{'keyword': name, 'count': count} for name, count in top_keywords]

    citation_stats = db.session.query(
      func.avg(Paper.citation_count).label('avg_citations'),
      func.max(Paper.citation_count).label('max_citations'),
      func.count(Paper.id).label('total_papers')
    ).first()

    trends['citation_statistics'] = {
      'average_citations': float(citation_stats.avg_citations or 0),
      'max_citations': citation_stats.max_citations or 0,
      'total_papers': citation_stats.total_papers
    }

    return jsonify({
      'trends': trends,
      'export_info': {
        'exported_at': func.now(),
        'data_types': ['papers_per_year', 'top_keywords', 'citation_statistics']
      }
    })

@bp.route('/export/full-database', methods=['GET'])
def export_full_database():

  try:
    papers = Paper.query.all()
    authors = Author.query.all()
    keywords = Keyword.query.all()
    citations = Citation.query.all()

    export_data = {
      'papers': [paper.to_dict() for paper in papers],
      'authors': [author.to_dict() for author in authors],
      'keywords': [keyword.to_dict() for keyword in keywords],
      'citations': [citation.to_dict() for citation in citations],
      'export_info': {
          'total_papers': len(papers),
          'total_authors': len(authors),
          'total_keywords': len(keywords),
          'total_citations': len(citations),
          'exported_at': func.now()
      }
    }

    return jsonify(export_data), 200
  
  except Exception as e:
    return jsonify({'error': str(e)}), 500

@bp.route('/upload/papers', methods=['POST'])
def upload_papers():
  if 'file' not in request.files:
    return jsonify({'error': 'No file provided'}), 400
  
  file = request.files['file']
  if file.filename == '':
    return jsonify({'error': 'No file selected'}), 400
  
  if not file.filename.lower().endswith(('.csv', '.json')):
    return jsonify({'error': 'Only CSV and JSON files supported'}), 400
  
  try: 
    if file.filename.lower().endswith('.csv'):
      stream = io.StringIO(file.stream.read().decode('UTF8'), newline=None)
      csv_input = csv.DictReader(stream)
      papers_data = list(csv_input)

    else:
      papers_data = json.loads(file.stream.read().decode('UTF8'))
      if not isinstance(papers_data, list):
        papers_data = papers_data.get('papers', [])

    created_count = 0
    errors=[]

    for i, paper_data in enumerate(papers_data):
      try:
        if 'title' not in paper_data or 'year' not in paper_data:
          errors.append(f'Row {i+1}: Missing title or year')
          continue
        
        paper = Paper(
          title = paper_data['title'],
          abstract=paper_data.get('abstract',''),
          year = int(paper_data['year']),
          citation_count=int(paper_data.get('citation_count', 0))
        )

        if 'authors' in paper_data:
          authors_list = paper_data['authors']
          if isinstance(authors_list, str):
            authors_list = [a.strip() for a in authors_list.split(';')]

          for author_name in authors_list:
            if author_name:
              author = Author.query.filter_by(name=author_name).first()
              if not author:
                author = Author(name=author_name)
                db.session.add(author)
              paper.authors.append(author)
        
        if 'keywords' in paper_data:
          keywords_list = paper_data['keywords']
          if isinstance(keywords_list, str):
            keywords_list = [k.strip() for k in keywords_list.split(';')]

          for keyword_name in keywords_list:
            if keyword_name:
              keyword = Keyword.query.filter_by(name=keyword_name.lower()).first()
              if not keyword:
                keyword = Keyword(name=keyword_name.lower())
                db.session.add(keyword)
              paper.keywords.append(keyword)

        db.session.add(paper)
        created_count += 1
      except Exception as e:
        errors.append(f'Row {i+1}: {str(e)}')
    db.session.commit()

    return jsonify({
      'message': f'Successfully uploaded {created_count} papers',
      'created_count': created_count,
      'total_processed': len(papers_data),
      'errors': errors[:10]
    }), 201
  
  except Exception as e:
    db.session.rollback()
    return jsonify({'error': f'File processing error: {str(e)}'}), 400
  
@bp.route('/validation/paper', methods=['POST'])
def validate_paper():
  data = request.get_json()

  errors = []

  if not data.get('title'):
    errors.append('Title is required')
  elif len(data['title']) > 500:
    errors.append('Title too long (max 500 characters)')

  if not data.get('year'):
    errors.append('Year is required')

  elif not isinstance(data['year'], int) or data['year'] < 1900 or data['year'] > 2030:
    errors.append('Invalid year (must be between 1900-2030)')

  if data.get('abstract') and len(data['abstract']) > 5000:
    errors.append('Abstract too long (max 500 characters)')

  if data.get('citation_count') and (not isinstance(data['citation_count'], int) or data['citation_count'] < 0):
    errors.append('Citation count must be non-negative integer')

  if data.get('title'):
    existing = Paper.query.filter_by(title=data['title']).first()
    if existing: 
      errors.append('Paper with this title already exists')

  return jsonify({
    'valid': len(errors) == 0,
    'errors': errors
  })

@bp.route('/health', methods=['GET'])
def health_check():

  try:
    db.session.execute('SELECT 1')
    db.status = 'healthy'
  
  except: 
    db_status = 'unhealthy'

  stats = {
    'papers': Paper.query.count(),
    'authors': Author.query.count(),
    'keywords': Keyword.query.count(),
    'citations': Citation.query.count()
  }
  
  return jsonify({
    'status': 'healthy' if db_status == 'healthy' else 'unhealthy',
    'message': 'ResearchExplorer API is running',
    'database': db_status,
    'statistics': stats,
    'endpoints': {
      'papers': '/api/papers',
      'search': '/api/search',
      'graph_data': '/api/graph/data',
      'trends': '/api/trends/*',
      'export': '/api/export/*',
      'analytics': '/api/analytics/*'
    }
  })

@bp.route('/statistics/overview', methods=['GET'])
@cache.cached(timeout=300)
def get_statistics():
  try:

    total_papers = Paper.query.count()
    total_authors = Author.query.count()
    total_keywords = Keyword.query.count()
    total_citations = Citation.query.count()

    citation_stats = db.session.query(
      func.avg(Paper.citation_count).label('avg'),
      func.max(Paper.citation_count).label('max'),
      func.min(Paper.citation_count).label('min')
    ).first()

    year_stats = db.session.query(
      func.min(Paper.year).label('min_year'),
      func.max(Paper.year).label('max_year')
    ).first()

    top_authors = db.session.query(
      Author.name,
      func.count(Paper.id).label('paper_count')
    ).join(Author.papers).group_by(Author.name)\
     .order_by(desc('paper_count')).limit(5).all()
    
    top_keywords = db.session.query(
      Keyword.name,
      func.count(Paper.id).label('paper_count')

    ).join(Keyword.papers).group_by(Keyword.name)\
     .order_by(desc('paper_count')).limit(5).all()
    
    return jsonify({
      'overview': {
        'total_papers': total_papers,
        'total_authors': total_authors,
        'total_keywords': total_keywords,
        'total_citations': total_citations
      },
      'citations': {
        'average': float(citation_stats.avg or 0),
        'maximum': citation_stats.max or 0,
        'minimum': citation_stats.min or 0
      },
      'years': {
        'earliest': year_stats.min_year,
        'latest': year_stats.max_year,
        'span': (year_stats.max_year - year_stats.min_year) if year_stats.min_year else 0
      },
      'top_authors': [{'name': name, 'papers': count} for name, count in top_authors],
      'top_keywords': [{'name': name, 'papers': count} for name, count in top_keywords]
    })
  
  except Exception as e:
    return jsonify({'error': str(e)}), 500
  

@bp.route('/statistics/trends', methods=['GET'])
@cache.cached(timeout=600)
def get_trending_stats():
  try:
    current_year = db.session.query(func.max(Paper.year)).scalar() or 2023
    recent_papers = Paper.query.filter(Paper.year >= current_year - 1).count()

    recent_highly_cited = Paper.query.filter(Paper.year >= current_year - 2)\
      .order_by(desc(Paper.citation_count)).limit(5).all()
    
    trending_keywords = db.session.query(
      Keyword.name,
      func.count(Paper.id).label('recent_count')
    ).join(Keyword.papers).filter(Paper.year >= current_year - 2)\
     .group_by(Keyword.name).order_by(desc('recent_count')).limit(10).all()

    return jsonify({
      'recent_activity': {
        'papers_last_2_years': recent_papers,
        'current_year_range': f"{current_year-1}-{current_year}"
      },
      'highly_cited_recent': [paper.to_dict() for paper in recent_highly_cited],
      'trending_keywords': [{'name': name, 'count': count} for name, count in trending_keywords]
    })
  
  except Exception as e:
    return jsonify({'error': str(e)}), 500
  

@bp.route('/maintenance/cleanup', methods=['POST'])
def cleanup_database():
  try:

    orphaned_authors = Author.query.filter(~Author.papers.any()).all()
    for author in orphaned_authors:
      db.session.delete(author)

    orphaned_keywords = Keyword.query.filter(~Keyword.papers.any()).all()
    for keyword in orphaned_keywords:
      db.session.delete(keyword)

    db.session.commit()

    return jsonify({
      'message': 'Database cleanup completed',
      'removed': {
        'authors': len(orphaned_authors),
        'keywords': len(orphaned_keywords)
      }
    })
  
  except Exception as e:
    db.session.rollback()
    return jsonify({'error': str(e)}), 500

@bp.route('/backup/create', methods=['POST'])
def create_backup():
  try:

    papers = Paper.query.all()
    authors = Author.query.all()
    keywords = Keyword.query.all()
    citations = Citation.query.all()

    backup_data = {
      'backup_info': {
        'created_at': func.now(),
        'total_records': {
          'papers': len(papers),
          'authors': len(authors),
          'keywords': len(keywords),
          'citations': len(citations)
        }
      },
      'data': {
        'papers': [paper.to_dict() for paper in papers],
        'authors': [author.to_dict() for author in authors],
        'keywords': [keyword.to_dict() for keyword in keywords],
        'citations': [citation.to_dict() for citation in citations]
      }
    }

    return jsonify({
      'message': 'Backup created successfully',
      'backup_data': backup_data
    })
  
  except Exception as e:
    return jsonify({'error': str(e)}), 500
    
    