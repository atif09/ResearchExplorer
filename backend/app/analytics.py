from app.models import Paper, Author, Keyword, Citation
from app import db
from sqlalchemy import func, desc
from collections import defaultdict
import networkx as nx
from datetime import datetime
      
class ResearchAnalytics:

  @staticmethod
  def get_research_hotspots(year_range=None, limit=10):
    query = db.session.query(
      Keyword.name,
      func.count(Paper.id).label('paper_count'),
      func.avg(Paper.citation_count).label('avg_citations')
    ).join(Keyword.papers)

    if year_range:
      start_year, end_year = year_range
      query = query.filter(Paper.year.between(start_year, end_year))

    results = query.group_by(Keyword.name)\
      .having(func.count(Paper.id) >= 3)\
      .order_by(desc('avg_citations'))\
      .limit(limit).all()

    return [
      {
        'keyword': keyword,
        'paper_count': paper_count,
        'avg_citations': float(avg_citations or 0),
        'hotspot_score': paper_count * float(avg_citations or 0)
      }
      for keyword, paper_count, avg_citations in results
    ]

@staticmethod
def get_author_collaborations_network(min_papers=2):
  authors = Author.query.join(Author.papers)\
    .group_by(Author.id)\
    .having(func.count(Paper.id) >= min_papers).all()

  collaborations = defaultdict(set)

  for author in authors:
    for paper in author.papers:
      co_authors = [a for a in paper.authors if a.id != author.id]
      for co_author in co_authors:
        collaborations[author.name].add(co_author.name)

  edges = []
  processed_pairs = set()

  for author, collaborators in collaborations.items():
    for collaborator in collaborators:
      pair = tuple(sorted([author, collaborator]))
      if pair not in processed_pairs:
        edges.append({
          'source':pair[0],
          'target': pair[1],
          'type': 'collaboration'
        })
        processed_pairs.add(pair)

  return {
    'nodes': [{'id': author.name, 'type': 'author', 'paper_count': len(list(author.papers))}
              for author in authors],
    'edges': edges
  }

@staticmethod
def analyze_citation_patterns():
  try:

    G = nx.DiGraph()

    papers = Paper.query.all()
    for paper in papers:
      G.add_node(paper.id, title=paper.title, year=paper.year)

    citations = Citation.query.all()
    for citation in citations:
      G.add_edge(citation.citing_paper_id, citation.cited_paper_id)

    if len(G.nodes()) == 0:
      return {
        'influential_papers': [],
        'network_stats': {
          'total_papers': 0,
          'total_citations': 0,
          'density': 0,
          'avg_clustering': 0
        }
      }
    
    pagerank_scores = nx.pagerank(G) if len(G.edges()) > 0 else {node: 0 for node in G.nodes()}
    betweenness_centrality = nx.betweenness_centrality(G) if len(G.edges()) > 0 else {node: 0 for node in G.nodes()}
    in_degree_centrality = nx.in_degree_centrality(G) if len(G.edges()) > 0 else {node: 0 for node in G.nodes()}


    influential_papers = []
    for paper_id, pagerank_score in sorted(pagerank_scores.items(),
                                           key=lambda x: x[1], reverse=True)[:20]:
      
      paper = Paper.query.get(paper_id)
      if paper:
        influential_papers.append({
          'id': paper.id,
          'title': paper.title,
          'year': paper.year,
          'citation_count': paper.citation_count,
          'pagerank_score': pagerank_score,
          'betweenness_centrality': betweenness_centrality.get(paper_id, 0),
          'in_degree_centrality': in_degree_centrality.get(paper_id, 0)
        })

    density = nx.desnity(G) if len(G.nodes()) > 1 else 0
    avg_clustering = nx.average_clustering(G.to_undirected()) if len(G.nodes()) > 1 else 0

    return {
      'influential_papers': influential_papers,
      'network_stats': {
        'total_papers': len(G.nodes()),
        'total_citations': len(G.edges()),
        'density': density,
        'avg_clustering': avg_clustering
      }
    }
  
  except Exception as e:

    papers=Paper.query.order_by(desc(Paper.citation_count)).limit(20).all()
    return {
      'influential_papers': [
        {
          'id': paper.id,
          'title': paper.title,
          'year': paper.year,
          'citation_count': paper.citation_count,
          'pagerank_score': 0,
          'betweenness_centrality': 0,
          'in_degree_centrality': 0
        }
        for paper in papers
      ],
      'network_stats': {
        'total_papers': Paper.query.count(),
        'total_citations': Citation.query.count(),
        'density': 0,
        'avg_clustering': 0
      }
    }
  
@staticmethod
def get_temporal_keyword_evolution(keyword, years_back=10):
  current_year = datetime.now().year
  start_year = current_year - years_back

  papers = Paper.query.join(Paper.keywords)\
    .filter(Keyword.name.contains(keyword.lower()))\
    .filter(Paper.year >= start_year)\
    .order_by(Paper.year).all()
  
  periods = defaultdict(list)
  for paper in papers:
    period = f'{paper.year//5 * 5}-{paper.year//5 * 5 + 4}'
    periods[period].append(paper)

  evolution = []
  for period, period_papers in sorted(periods.items()):
    co_keywords = defaultdict(int)
    total_citations = 0

    for paper in period_papers:
      total_citations += paper.citation_count
      for kw in paper.keywords:
        if kw.name != keyword.lower():
          co_keywords[kw.name] += 1
    
    top_co_keywords = sorted(co_keywords.items(),
                             key=lambda x: x[1], reverse=True)[:10]
    
    evolution.append({
      'period': period,
      'paper_count': len(period_papers),
      'avg_citations': total_citations / len(period_papers) if period_papers else 0,
      'top_co_keywords': [{'keyword': kw, 'count': count}
                          for kw, count in top_co_keywords]
    })

  return {
    'keyword': keyword,
    'evolution': evolution,
    'total_papers': len(papers)
  }

@staticmethod
def identify_research_papers(min_citations= 50, max_recent_papers=5):
  current_year = datetime.now().year
  recent_year_threshold = current_year - 3

  gaps =[]

  old_influential = Paper.query\
    .filter(Paper.citation_count >= min_citations)\
    .filter(Paper.year , recent_year_threshold)\
    .all()
  
  for paper in old_influential:
    recent_similar = 0
    for keyword in paper.keywords:
      recent_count = Paper.query.join(Paper.keywords)\
        .filter(Keyword.name == keyword.name)\
        .filter(Paper.year >= recent_year_threshold)\
        .count()
      recent_similar += recent_count

    avg_recent_similar = recent_similar / max(len(paper.keywords), 1)

    if avg_recent_similar <= max_recent_papers:
      gaps.append({
        'paper': paper.to_dict(),
        'recent_similar_papers': avg_recent_similar,
        'keywords': [kw.name for kw in paper.keywords],
        'gap_score': paper.citation_count / max(avg_recent_similar, 1)
      })

  gaps.sort(key=lambda x: x['gap_score'], reverse=True)
  return gaps[:20]

@staticmethod
def get_collaboration_strength(author1_name, author2_name):
  try:
    author1 = Author.query.filter_by(name=author1_name).first()
    author2 = Author.query.filter_by(name=author2_name).first()

    if not author1 or not author2:
      return 0
    
    common_papers = db.session.query(Paper)\
      .join(paper_authors, Paper.id == paper_authors.c.paper_id)\
      .filter(paper_authors.c.author_id.in_([author1.id, author2.id]))\
      .group_by(Paper.id)\
      .having(func.count(paper_authors.c.author_id) == 2)\
      .all()
    
    return len(common_papers)
  
  except Exception as e:
    return 0 

@staticmethod
def get_keyword_relationships(keyword_name, limit=10):
  try:
    keyword = Keyword.query.filter_by(name=keyword_name.lower()).first()
    if not keyword:
      return []
    
    papers_with_keyword = keyword.papers.all()

    co_occurence = defaultdict(int)
    for paper in papers_with_keyword:
      for kw in paper.keywords:
        if kw.name != keyword_name.lower():
          co_occurence[kw.name] += 1

    related_keywords = sorted(co_occurence.items(),
                               key=lambda x: x[1], reverse=True)[:limit]
    
    return [
      {
        'keyword': kw,
        'co_occurence_count': count,
        'strength': count / len(papers_with_keyword)

      }
      for kw, count in related_keywords
    ]
  
  except Exception as e:
    return []
  
@staticmethod
def get_author_impact_metrics(author_name):
  try:
    author = Author.query.filter_by(name=author_name).first()
    if not author:
      return None
    
    papers = list(author.papers)
    if not papers:
      return None
    
    total_papers = len(papers)
    total_citations = sum(paper.citation_count for paper in papers)
    avg_citations = total_citations / total_papers if total_papers > 0 else 0

    citation_counts = sorted([paper.citation_count for paper in papers], reverse=True)
    h_index = 0
    for i, citations in enumerate(citation_counts):
      if citations >= i+1:
        h_index = i+1
      else:
        break
    
    current_year = datetime.now().year
    recent_papers = [p for p in papers if p.year >= current_year - 3]

    collaborators = set()
    for paper in papers:
      collaborators.update([a.name for a in paper.authors if a.name != author_name])

    return {
      'author': author_name,
      'total_papers': total_papers,
      'total_citations': total_citations,
      'avg_citations': avg_citations,
      'h_index': h_index,
      'recent_papers_count': len(recent_papers),
      'unique_collaborators': len(collaborators),
      'most_cited_paper': max(papers, key=lambda p: p.citation_count).to_dict() if papers else None,
      'active_years': list(set(paper.year for paper in papers))
    }
  
  except Exception as e:
    return None
  
