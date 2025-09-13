#!/usr/bin/env python3
import os
import sys
import click
import json
from datetime import datetime
from flask.cli import with_appcontext
from app import create_app, db

app = create_app(os.getenv('FLASK_ENV', 'development'))

@app.shell_context_processor
def make_shell_context():
    from app.models import (
        Paper, Author, Keyword, Citation, 
        paper_authors, paper_keywords,
        create_sample_data, backup_database, restore_database
    )
    from app.analytics import ResearchAnalytics
    from app.utils import DataProcessor, FileManager
    
    return {
        'db': db,
        'Paper': Paper,
        'Author': Author,
        'Keyword': Keyword,
        'Citation': Citation,
        'paper_authors': paper_authors,
        'paper_keywords': paper_keywords,
        'create_sample_data': create_sample_data,
        'backup_database': backup_database,
        'restore_database': restore_database,
        'analytics': ResearchAnalytics,
        'DataProcessor': DataProcessor,
        'FileManager': FileManager
    }

@app.cli.command()
@click.option('--drop-first', is_flag=True, help='Drop all tables before creating')
def init_db(drop_first):

    if drop_first:
        if click.confirm('This will delete all existing data. Are you sure?'):
            click.echo('Dropping all tables...')
            db.drop_all()
        else:
            click.echo('Operation cancelled.')
            return
    
    click.echo('Creating all tables...')
    db.create_all()
    click.echo('Database initialized successfully!')

@app.cli.command()
@click.option('--skip-if-exists', is_flag=True, help='Skip if sample data already exists')
def create_sample_data_cmd(skip_if_exists):

    from app.models import create_sample_data, Paper
    
    if skip_if_exists and Paper.query.count() > 0:
        click.echo('Sample data already exists. Use --drop-first to recreate.')
        return
    
    click.echo('Creating sample data...')
    try:
        create_sample_data()
        click.echo('Sample data created successfully!')
    except Exception as e:
        click.echo(f'Error creating sample data: {str(e)}', err=True)
        sys.exit(1)

@app.cli.command()
def reset_db():
    if click.confirm('This will delete all data. Are you sure?'):
        click.echo('Dropping all tables...')
        db.drop_all()
        click.echo('Recreating all tables...')
        db.create_all()
        click.echo('Database reset successfully!')
    else:
        click.echo('Operation cancelled.')

@app.cli.command()
@click.option('--output', '-o', help='Output file path (optional)')
def backup_db(output):
    from app.models import backup_database
    
    try:
        click.echo('Creating database backup...')
        
        if output:
   
            backup_data = backup_database()
            click.echo(f'Database backed up to {backup_data}')
        else:
   
            backup_file = backup_database()
            click.echo(f'Database backed up to {backup_file}')
            
    except Exception as e:
        click.echo(f'Error creating backup: {str(e)}', err=True)
        sys.exit(1)

@app.cli.command()
@click.argument('backup_file')
@click.option('--confirm', is_flag=True, help='Skip confirmation prompt')
def restore_db(backup_file, confirm):

    from app.models import restore_database
    
    if not os.path.exists(backup_file):
        click.echo(f'Backup file {backup_file} not found!', err=True)
        sys.exit(1)
    
    if not confirm and not click.confirm('This will replace all current data. Are you sure?'):
        click.echo('Operation cancelled.')
        return
    
    try:
        click.echo(f'Restoring database from {backup_file}...')

        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
 
        result = restore_database(backup_data)
        click.echo('Database restored successfully!')
        click.echo(f'Restored: {result}')
        
    except Exception as e:
        click.echo(f'Error restoring backup: {str(e)}', err=True)
        sys.exit(1)

@app.cli.command()
def check_health():

    try:

        db.session.execute('SELECT 1')
   
        from app.models import Paper, Author, Keyword, Citation
        stats = {
            'papers': Paper.query.count(),
            'authors': Author.query.count(),
            'keywords': Keyword.query.count(),
            'citations': Citation.query.count()
        }
        
        click.echo('Application is healthy')
        click.echo(f'Database statistics:')
        for entity, count in stats.items():
            click.echo(f'   - {entity.capitalize()}: {count}')
        
        directories = [
            app.config['UPLOAD_FOLDER'],
            app.config['EXPORT_FOLDER'],
            app.config['BACKUP_FOLDER']
        ]
        
        click.echo('Directory status:')
        for directory in directories:
            if os.path.exists(directory):
                file_count = len(os.listdir(directory))
                click.echo(f'   - {directory}: {file_count} files')
            else:
                click.echo(f'   - {directory}: Missing')
        
    except Exception as e:
        click.echo(f'Application health check failed: {str(e)}', err=True)
        sys.exit(1)

@app.cli.command()
@click.option('--limit', default=5, help='Number of results to show')
def run_analytics(limit):
    """Run research analytics and display results"""
    try:
        from app.analytics import ResearchAnalytics
        
        click.echo('Running research analytics...')
   
        click.echo('\n📈 Top Research Hotspots:')
        hotspots = ResearchAnalytics.get_research_hotspots(limit=limit)
        for i, hotspot in enumerate(hotspots, 1):
            click.echo(f'   {i}. {hotspot["keyword"]} '
                      f'({hotspot["paper_count"]} papers, '
                      f'{hotspot["avg_citations"]:.1f} avg citations)')
        
        click.echo('\n🔗 Citation Network Analysis:')
        patterns = ResearchAnalytics.analyze_citation_patterns()
        stats = patterns["network_stats"]
        click.echo(f'   - Total papers: {stats["total_papers"]}')
        click.echo(f'   - Total citations: {stats["total_citations"]}')
        click.echo(f'   - Network density: {stats["density"]:.4f}')
        click.echo(f'   - Average clustering: {stats["avg_clustering"]:.4f}')

        if patterns["influential_papers"]:
            click.echo('\n🏆 Most Influential Papers:')
            for i, paper in enumerate(patterns["influential_papers"][:limit], 1):
                click.echo(f'   {i}. {paper["title"][:60]}... '
                          f'({paper["citation_count"]} citations)')
        
        click.echo('\nAnalytics completed!')
        
    except Exception as e:
        click.echo(f'Analytics failed: {str(e)}', err=True)
        sys.exit(1)

@app.cli.command()
@click.option('--days', default=7, help='Clean files older than N days')
def cleanup(days):
    """Clean up old temporary files"""
    try:
        from app.utils import FileManager
        
        directories = [
            app.config['UPLOAD_FOLDER'],
            app.config['EXPORT_FOLDER']
        ]
        
        click.echo(f'🧹 Cleaning files older than {days} days...')
        
        for directory in directories:
            if os.path.exists(directory):
                FileManager.cleanup_old_files(directory, days)
                click.echo(f'Cleaned {directory}')
        
        click.echo('Cleanup completed!')
        
    except Exception as e:
        click.echo(f'Cleanup failed: {str(e)}', err=True)
        sys.exit(1)

@app.cli.command()
@click.option('--port', default=5000, help='Port to run the server on')
@click.option('--host', default='127.0.0.1', help='Host to bind to')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def runserver(port, host, debug):
    """Run the development server"""
    env = os.getenv('FLASK_ENV', 'development')
    
    click.echo('Starting Research Explorer')
    click.echo(f'   Environment: {env}')
    click.echo(f'   Host: {host}')
    click.echo(f'   Port: {port}')
    click.echo(f'   Debug: {"enabled" if debug else "disabled"}')
    click.echo(f'   Database: {app.config["SQLALCHEMY_DATABASE_URI"]}')
    click.echo(f'   Available at: http://{host}:{port}/api/health')
    
    app.run(host=host, port=port, debug=debug)

@app.cli.command()
def routes():
    click.echo('Registered Routes:')
    
    routes = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        routes.append((rule.endpoint, methods, str(rule)))

    routes.sort()
    
    for endpoint, methods, rule in routes:
        click.echo(f'   {methods:<10} {rule:<50} {endpoint}')

@app.cli.command()
def show_config():
    click.echo('Current Configuration:')
    
    config_items = [
        ('Environment', os.getenv('FLASK_ENV', 'development')),
        ('Debug', app.config.get('DEBUG')),
        ('Database URI', app.config.get('SQLALCHEMY_DATABASE_URI')),
        ('Cache Type', app.config.get('CACHE_TYPE')),
        ('Upload Folder', app.config.get('UPLOAD_FOLDER')),
        ('Backup Folder', app.config.get('BACKUP_FOLDER')),
        ('Max Content Length', f"{app.config.get('MAX_CONTENT_LENGTH', 0) // (1024*1024)}MB"),
        ('Auto Backup', app.config.get('AUTO_BACKUP_ENABLED'))
    ]
    
    for key, value in config_items:
        click.echo(f'   {key:<20}: {value}')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        print("Research Explorer Backend")
        print(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
        print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"Starting server on http://0.0.0.0:5000")
        print("Available endpoints:")
        print("  - Health: http://0.0.0.0:5000/api/health")
        print("  - Papers: http://0.0.0.0:5000/api/papers")
        print("  - Analytics: http://0.0.0.0:5000/api/analytics/research-hotspots")
        print("\nUse 'flask --help' to see available CLI commands")
        
    app.run(debug=True, host='0.0.0.0', port=5000)