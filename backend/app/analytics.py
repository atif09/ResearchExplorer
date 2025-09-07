from app.models import Paper,Author, Keyword,Citation
from app import db
from sqlalchemy import func,desc
from collections import defaultdict
import networkx as nx

class ResearchAnalytics:
  
  @staticmethod
  def get_research_hotspots(year_range=None, limit=10):
    query