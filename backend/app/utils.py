import csv
import json
import io
import os
import pandas as pd
from datetime import datetime
from flask import current_app
from typing import List, Dict, Any, Optional
from werkzeug.utils import secure_filename
import validators

def allowed_file(filename: str, allowed_extensions: set = None) -> bool: 
  if allowed_extensions is None:
    allowed_extensions ={'csv', 'json', 'txt', 'xlsx'}

  return '.' in filename and \
    filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_uploaded_file(file, folder: str = None) -> str:
  if folder is None:
    folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')

  if not os.path.exists(folder):
    os.makedirs(folder)

  filename = secure_filename(file.filename)
  timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
  filename = f'{timestamp}_{filename}'
  filepath = os.path.join(folder, filename)

  file.save(filepath)
  return filepath

def export_to_csv(data: List[Dict], filename: str = None) -> str:
  if not data:
    return ''
  
  output = io.StringIO()
  writer = csv.DictWriter(output, fieldnames=data[0].keys())
  writer.writerheader()
  writer.writerows(data)

  return output.getvalue()

def export_to_json(data: Any, filename: str = None) -> str:
  return json.dumps(data, indent=2, default=str)

def parse_csv_file(filepath: str) -> List[Dict]:
  try: 
    df = pd.read_csv(filepath)
    return df.to_dict('records')
  except Exception as e:
    raise ValueError(f'Error parsing CSV file: {str(e)}')
  
def parse_json_file(filepath: str) -> Dict:
  try: 
    with open(filepath, 'r', encoding='utf-8') as f:
      return json.load(f)
  except Exception as e:
    raise ValueError(f'Error parsing JSON file: {str(e)}')
  
def validate_year_range(year_from: int = None, year_to: int = None) -> bool:
  current_year = datetime.now().year

  if year_from and (year_from < 1900 or year_from > current_year + 5):
    return False
  
  if year_to and (year_to < 1900 or year_to > current_year + 5):
    return False
  
  if year_from and year_to and year_from > year_to:
    return False
  
  return True

def validate_pagination(page: int=1, per_page: int=20) -> tuple:
  page = max(1, page)
  per_page = min(max(1, per_page), current_app.config.get('MAX-SEARCH_RESULTS', 1000))

  return page, per_page

def normalize_keyword(keyword: str) -> str:
  return keyword.lower().strip()

def normalize_author_name(name: str) -> str:
  return ' '.join(name.strip().split()).title()

def calculate_similarity_score(text1: str, text2: str) -> float:
  if not text1 or not text2:
    return 0.0
  
  words1 = set(text1.lower().split())
  words2 = set(text2.lower().split())

  if not words1 or not words2:
    return 0.0

  intersection = words1.intersection(words2)
  union = words1.union(words2)

  return len(intersection) / len(union) if union else 0.0

def clean_text(text: str) -> str:
  if not text:
    return ''
  
  return ' '.join(text.strip().split())

def validate_url(url: str) -> bool:
  return validators.url(url)

def generate_export_filename(base_name: str, format_type: str = 'json') -> str:
  timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
  return f'{base_name}_{timestamp}.{format_type}'

def paginate_results(query, page: int,per_page:int):
  total = query.count()
  items = query.offset((page-1) * per_page).limit(per_page).all()

  return {
    'items': items,
    'total': total,
    'pages': (total + per_page - 1) // per_page,
    'current_page': page,
    'per_page': per_page,
    'has_next': page * per_page < total,
    'has_prev': page > 1
  }

def format_api_response(data: Any, message: str = None, status: str = 'success') -> Dict:
  response = {
    'status': status,
    'data': data

  }

  if message: 
    response['message'] = message

  return response

def log_api_usage(endpoint: str, user_id: str = None, params: Dict = None):
  current_app.logger.info(f'API Usage - Endpoint: {endpoint}, User: {user_id}, Params: {params}')

class DataProcessor:

  @staticmethod
  def extract_keywords_from_text(text: str, existing_keywords: List[str] = None) -> List[str]:
    if not text:
      return []
    
    words = text.lower().split()

    stop_words = {
      'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
      'of', 'with', 'by', 'a', 'an', 'is', 'are', 'was', 'were',
      'this', 'that', 'these', 'those', 'from', 'up', 'down'

    }

    keywords = [
      word.strip('.,!?:;')
      for word in words
      if len(word) > 3 and word not in stop_words
    ]

    unique_keywords = list(dict.fromkeys(keywords))

    return unique_keywords[:10]

@staticmethod
def suggest_similar_papers(paper_title: str, existing_papers: List = None) -> List[Dict]:
  if not existing_papers:
    return []
  
  suggestions = []
  for paper in existing_papers:
    similarity = calculate_similarity_score(paper_title, paper.title)
    if similarity > 0.3:
      suggestions.append({
        'paper': paper.to_dict(),
        'similarity_score': similarity
      })

  suggestions.sort(key=lambda x: x['similarity_score'], reverse=True)
  return suggestions[:5]

@staticmethod
def detect_duplicates(papers_data: List) -> List[Dict]:
  duplicates = []
  processed = []

  for i, paper in enumerate(papers_data):
    for j, existing in enumerate(processed):
      similarity = calculate_similarity_score(
        paper.get('title', ''),
        existing.get('title', '')
      )
      if similarity > 0.8:
        duplicates.append({
          'paper1_index': j,
          'paper2_index': i,
          'similarity': similarity,
          'paper1_title': existing.get('title'),
          'paper2_title': paper.get('title')
        })
    processed.append(paper)

  return duplicates

@staticmethod
def validate_paper_data(paper_data: Dict) -> List[str]:
  errors =[]

  if not paper_data.get('title'):
    errors.append('Title is required.')
  elif len(paper_data['title']) > 500:
    errors.append('Title too long (max 500 characters)')

  if not paper_data.get('year'):
    errors.append('Year is required.')

  else:
    try:
      year = int(paper_data['year'])
      if year < 1900 or year > datetime.now().year + 5:
        errors.append('Invalid year range')
    except (ValueError, TypeError):
      errors.append('Year must be a number')

  if paper_data.get('abstract') and len(paper_data['abstract']) > 5000:
    errors.append('Abstract too long (max 5000 characters)')

  if paper_data.get('citation_count'):
    try:
      citations = int(paper_data['citation_count'])
      if citations < 0:
        errors.append('Citation count cannot be negative')
    except (ValueError, TypeError):
      errors.append('Citation count must be a number')

  return errors

class FileManager:

  @staticmethod
  def ensure_directory_exists(directory: str):
    if not os.path.exists(directory):
      os.makedirs(directory, exist_ok=True)

  @staticmethod
  def cleanup_old_files(directory: str, max_age_days: int = 7):

    if not os.path.exists(directory):
      return
    
    cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)

    for filename in os.listdir(directory):
      filepath = os.path.join(directory, filename)
      if os.path.isfile(filepath):
        file_time = os.path.getctime(filepath)
        if file_time < cutoff_time:
          try: 
            os.remove(filepath)
            current_app.logger.info(f'Cleaned up old file: {filepath}')
          except OSError as e:
            current_app.logger.error(f'Error removing file {filepath}: {e}')

  @staticmethod
  def get_file_info(filepath: str) -> Dict:
    if not os.path.exists(filepath):
      return {}
    
    stat = os.stat(filepath)

    return {
      'size': stat.st_size,
      'created': datetime.fromtimestamp(stat.st_ctime),
      'modified': datetime.fromtimestamp(stat.st_mtime),
      'extension': os.path.splitext(filepath)[1].lower()
    }
  
class CacheHelper:

  @staticmethod
  def generate_cache_key(prefix: str, **kwargs) -> str:
    key_parts = [prefix]
    for k, v in sorted(kwargs.items()):
      if v is not None:
        key_parts.append(f'{k}_{v}')
    return '_'.join(key_parts)
  
  @staticmethod #REDISSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS
  def invalidate_related_cache(patterns: List[str]):
    pass

class ValidationHelper: 
  @staticmethod
  def validate_search_params(params: Dict) -> List[str]: 
    errors = []

    if params.get('year_from') and params.get('year_to'):
      if params['year_from'] > params['year_to']:
        errors.append('year_from cannot be greater than year_to')

    if params.get('min_citations') and params.get('max_citations'):
      if params['min_citations'] > params['max_citations']:
        errors.append('min_citations cannot be greater than max_citations')

    return errors
  
  @staticmethod
  def sanitize_input(text: str) -> str:
    if not text:
      return ''

    dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
    sanitized = text
    for char in dangerous_chars:
      sanitized = sanitized.replace(char, '')

    return sanitized.strip()
  
def dict_to_csv_row(data: Dict, headers: List[str]) -> List:
  return [data.get(header, '') for header in headers]

def flatten_nested_dict(data: Dict, separator: str = '_') -> Dict:
  def _flatten(obj, parent_key=''):
    items =[]
    for key, value in obj.items():
      new_key = f'{parent_key}{separator}{key}' if parent_key else key
      if isinstance(value, dict):
        items.extend(_flatten(value, new_key).items())
      elif isinstance(value, list):
        items.append((new_key, ';'.join(str(v) for v in value)))
      else:
        items.append((new_key, value))
    return dict(items)
  
  return _flatten(data)

from typing import Generator

def chunk_list(lst: List, chunk_size: int) -> Generator[List, None, None]:
  for i in range(0, len(lst), chunk_size):
    yield lst[i:i + chunk_size]


