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

def allowed_file(filename: str, allowed_extensions: set=None) -> bool:
  if allowed_extensions is None:
    allowed_extensions = {'csv', 'json', 'txt', 'xlsx'}

  return '.' in filename and \
  filename.rsplit('.', 1)[1].lower(0 in allowed_extensions)

def save_uploaded_file(file, folder: str=None) -> str:
  if folder is None:
    folder = current_app.config['UPLOAD_FOLDER']

  if not os.path.exists(folder):
    os.makedirs(folder)

  filename = secure_filename(file.filename)
  timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
  filename = f'{timestamp}_{filename}'
  filepath = os.path.join(folder,filename)

  file.save(filepath)
  return filepath

def export_to_csv(data: List[Dict], filename: str=None) -> str:
  if not data:
    return ''
  
  output = io.StringIO()
  writer = csv.DictWriter(output, fieldnames=data[0].keys())
  writer.writeheader()
  writer.writerows(data)

  return output.getvalue()

def export_to_json(data: Any, filename: str = None) -> str:
  return json.dumps(data, indent=2, default=str)

def parse_csv_file(filepath: str) -> List[Dict]:
  try: 
    df=pd.read_csv(filepath)
    return df.to_dict('records')
  except Exception as e:
    raise ValueError(f'Error parsing CSV file: {str(e)}')

def parse_json_file(filepath: str) ->Dict:
  try:
    with open(filepath, 'r', encoding='utf-8') as f:
      return json.load(f)
    
  except Exception as e:
    raise ValueError(f'Error parsing JSON file: {str(e)}')
  
def validate_year_range(year_from: int = None, year_to: int = None) -> bool:
  current_year=datetime.now().year

  if year_to and (year_to < 1900 or year_from > current_year + 5):
    return False
  
  if year_to and (year_to < 1900 or year_to > current_year + 5):
    return False

  return True

def validate_pagination(page: int=1, per_page: int=20) -> tuple:
  page=max(1, page)
  per_page=min(max(1,per_page), current_app.config.get('MAX_SEARCH_RESULTS', 1000))

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

  return len(intersection) / len(union)

def clean_text(text: str) -> str:
  if not text:
    return ''
  
  return ' '.join(text.strip().split())

def validate_url(url: str) -> bool:
  return validators.url(url)

def generate_export_filename(base_name: str, format_type: str='json') -> str:
  timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
  return f'{base_name}_{timestamp}.{format_type}'

def paginate_results(query, page: int, per_page: int):
  total=query.count()
  items=query.offset((page - 1) * per_page).limit(per_page).all()

  return {
    'items': items,
    'total': total,
    'pages': (total + per_page - 1) // per_page,
    'current_page': page,
    'per_page': per_page,
    'has_next': page * per_page < total,
    'has_prev': page > 1
  }

def format_api_response(data: Any, message: str=None, status: str = 'success') -> Dict:
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
  def extract_keywords_from_text(text: str, existing_keywords: List[str]= None) -> List[str]:
    if not text:
      return []
    
    words = text.lower().split()

    stop_words = {'the', 'and', 'or', 'but', 'in','on','at','to','for','of','with','by'}
    keywords = [word.strip('.,!?:;') for word in words
                if len(word) > 3 and word not in stop_words]

    unique_keywords = list(dict.fromkeys(keywords))

    return unique_keywords[:10] 
  
  @staticmethod
  def suggest_similar_papers(paper_title: str, existing_papers: List=None) -> List[Dict]:
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
  

class FileManager:
  @staticmethod
  def ensure_directory_exists(directory: str):
    if not os.path.exists(directory):
      os.makedirs(directory)

  @staticmethod
  def cleanup_old_files(directory: str, max_age_days: int=7):
    if not os.path.exists(directory):
      return
    
    cutoff_time=datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)

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


class CacheHelper:

  @staticmethod
  def generate_cache_key(prefix: str, **kwargs) -> str:
    key_parts = [prefix]
    for k, v in sorted(kwargs.items()):
      if v is not None:
        key_parts.append(f'{k}_{v}')
    return '_'.join(key_parts)
  
  @staticmethod
  def invalidate_related_cache(patterns: List[str]):
    pass

