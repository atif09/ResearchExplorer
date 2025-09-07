from app.models import Paper,Author, Keyword,Citation
from app import db
from sqlalchemy import func,desc
from collections import defaultdict
import networkx as nx

class ResearchAnalytics:
  
  @staticmethod
  def get_research_hotspots(year_range=None, limit=10):
    query=db.session.query(
      Keyword.name,
      func.count(Paper.id).label('paper_count'),
      func.avg(Paper.citation_count).label('avg_citations')
    ).join(Keyword.papers)

    if year_range:
      start_year, end_year=year_range
      query=query.filter(Paper.year.between(start_year, end_year))

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
  def get_author_collaboration_network(min_papers=2):
    authors = Author.query.join(Author.papers)\
      .group_by(Author.id)\
      .having(func.count(Paper.id) >= min_papers).all()
    
    collborations = defaultdict(set)

    for author in authors:
      for paper in author.papers: 
        co_authors = [a for a in paper.authors if a.id != author.id]
        for co_author in co_authors:
          collaborations[author.name].add(co_author.name)

    edges=[]
    processed_pairs=set()

    for author, collaborators in collaborations.items():
      for collaborator in collaborators:
        pair = tuple(sorted([author,collaborator]))
        if pair not in processed_pairs:
          edges.append({
            'source': pair[0],
            'target': pair[1],
            'type': 'collaborations'
          })
          processed_pairs.add(pair)

    return {
      'nodes': [{'id': author.name, 'type': 'author', 'paper_count': author.papers.count()}
                for author in authors],
      'edges': edges
    }
  
  @staticmethod
  def analyze_citation_patterns():

    G=nx.DiGraph()

    papers = Paper.query.all()
    for paper in papers: 
      G.add_node(paper.id, title=paper.title, year=paper.year)

    citations = Citation.query.all()
    for citation in citations:
      G.add_edge(citation.citing_paper_id, citation.cited_paper_id)

    pagerank_scores = nx.pagerank(G)
    betweenness_centrality = nx.betweenness_centrality(G)
    in_degree_centrality = nx.in_degree_centrality(G)

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
            'pagerank_Score': pagerank_score,
            'betweenness_centrality': betweenness_centrality.get(paper_id, 0),
            'in_degree_centrality': in_degree_centrality.get(paper_id, 0)
          })
    return {
      'influential_papers': influential_papers,
      'network_stats': {
        'total_papers': len(G.nodes()),
        'total_citations': len(G.edges()),
        'density': nx.density(G),
        'avg_clustering': nx.average_clustering(G.to_undirected())
      }
    }
  
  @staticmethod
  def get_temporal_keyword_evolution(keyword, years_back=10):

    from datetime import datetime

    current_year = datetime.now().year
    start_year = current_year - years_back

    papers = Paper.query.join(Paper.keywords)\
      .filter(Keyword.name.contains(Keyword.lower()))\
      .filter(Paper.year >= start_year)\
      .order_by(Paper.year).all()
    
    periods = defaultdict(list)
    for paper in papers:
      period = f'{paper.year//5 * 5}-{paper.year//5 * 5 + 4}'
      periods[period].append(paper)

    evolution = []
    for period, period_papers in periods.items():

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
  def identify_research_gaps(min_citations=50, max_recent_papers=5):

    from datetime import datetime

    current_year = datetime.now().year
    recent_year_threshold = current_year - 3

    gaps = []

    old_influential = Paper.query\
      .filter(Paper.citation_count >= min_citations)\
      .filter(Paper.year < recent_year_threshold)\
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
      
      