from marshmallow import Schema, fields, validate, post_load, ValidationError
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models import Paper, Author, Keyword, Citation
from app import ma


class AuthorSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = Author
    load_instance = True
    include_relationships =True

  paper_count = fields.Method('get_paper_count')

  def get_paper_count(self,obj):
    return obj.papers.count() if obj.papers else 0
  
class KeywordSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = Keyword
    load_instance = True
    include_relationships = True

  paper_count = fields.Method('get_paper_count')

  def get_paper_count(self, obj):
    return obj.papers.count() if obj.papers else 0
  
class PaperSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = Paper
    load_instance = True
    include_relationships = True

  authors = fields.Nested(AuthorSchema, many=True, exclude=['papers'])
  keywords = fields.Nested(KeywordSchema, many=True, exclude=['papers'])

  title = fields.Str(required=True, validate=validate.length(min=1, max=500))
  year = fields.Int(required=True, validate=validate.Range(min=1900, max=2030))
  citation_count = fields.Int(validate=validate.Range(min=0))

class CitationSchema(SQLAlchemyAutoSchema):
  class Meta:
    model = Citation
    load_instance = True

  citing_paper_title = fields.Method('get_citing_paper_title')
  cited_paper_title = fields.Method('get_cited_paper_title')

  def get_citing_paper_title(self, obj):
    return obj.citing_paper.title if obj.citing_paper else None
  
  def get_cited_paper_title(self, obj):
    return obj.cited_paper.title if obj.cited_paper else None
  
class PaperCreateSchema(Schema):
  title = fields.Str(required=True, validate=validate.Length(min=1, max=500))
  abstract = fields.Str(validate=validate.Length(max=5000))
  year = fields.Int(required=True, validate=validate.Range(min=1900, max=2030))
  citation_count = fields.Int(validate=validate.Range(min=0))
  authors = fields.List(fields.Str(validate=validate.Length(min=1, max=200)))
  keywords = fields.List9fields.Str(validate=validate.Length(min=1, max=100))

class SearchSchema(Schema):
  query=fields.Str(validate=validate.Length(max=200))
  author=fields.Str(validate=validate.Length(max=200))
  keyword = fields.Str(validate=validate.Length(max=100))
  year_from = fields.Int(validate=validate.Range(min=1900, max=2030))
  year_to = fields.Int(validate=validate.Range(min=1900, max=2030))
  min_citations = fields.Int(validate=validate.Range(min=0))
  max_citations = fields.Int(validate=validate.Range(min=0))
  page = fields.Int(validate=validate.Range(min=1))
  per_page = fields.Int(validate = validate.Range(min=1, max=100))

class GraphFilterSchema(Schema):
  year_from = fields.Int(validate=validate.Range(min=1900, max=2030))
  year_to = fields.Int(validate=validate.Range(min=1900, max=2030))
  keyword = fields.Str(validate=validate.Length(max=100))
  max_nodes = fields.Int(validate=validate.Range(min=1, max=10000))
  min_citations = fields.Int(validate=validate.Range(min=0))  

class BulkPaperSchema(Schema):
  papers=fields.List(fields.Nested(PaperCreateSchema), required=True,
                     validate=validate.Length(min=1, max=1000))
  
class AdvancedSearchSchema(Schema):
  text = fields.Str(validate=validate.Length(max=500))
  authors = fields.List(fields.Str(validate=validate.Length(max=200)))
  keywords = fields.List(fields.Str(validate=validate.Length(max=100)))
  citation_range = fields.Dict()
  year_range = fields.Dict()
  sort_by = fields.Str(validate=validate.OneOf(['year', 'citations', 'title']))
  sort_order = fields.Str(validate=validate.OneOf(['asc', 'desc']))
  page = fields.Int(validate=validate.Range(min=1))
  per_page = fields.Int(validate=validate.Range(min=1, max=100))

paper_schema = PaperSchema()
papers_schema = PaperSchema(many=True)
author_schema = AuthorSchema()
authors_schema = AuthorSchema(many=True)
keyword_schema = KeywordSchema()
keywords_schema = KeywordSchema(many=True)
citation_schema = CitationSchema()
citations_schema = CitationSchema(many=True)  