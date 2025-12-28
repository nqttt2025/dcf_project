#!/usr/bin/env python3
"""
Flask Web Service for DCF Analysis Dashboard
"""
import os
import json
import sys
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.result_manager import get_result_manager
from src.utils.config_manager import ConfigManager

app = Flask(__name__)
CORS(app)

# Initialize managers
result_manager = get_result_manager()
config_dir = project_root / 'config'
results_dir = project_root / 'data' / 'results'
cache_dir = project_root / 'data' / 'cache'

# Track running processes (simple in-memory store)
running_processes = {}


@app.route('/')
def index():
    """Dashboard homepage"""
    return render_template('index.html')


@app.route('/api/stocks')
def get_stocks():
    """Get list of all stocks with their status"""
    stocks = []
    
    # Get all config files
    config_files = sorted(config_dir.glob('*.cfg'))
    
    for config_file in config_files:
        ticker = config_file.stem.upper()
        if ticker == 'README':
            continue
        
        # Check if result exists
        result_file = results_dir / f'{ticker.lower()}_result.json'
        has_result = result_file.exists()
        
        # Load result if exists
        result_data = None
        if has_result:
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    result_data = json.load(f)
            except:
                pass
        
        # Check if running
        is_running = ticker in running_processes
        
        stock_info = {
            'ticker': ticker,
            'has_result': has_result,
            'is_running': is_running,
            'current_price': result_data.get('price') if result_data else None,
            'dcf_fair_value': result_data.get('dcf_fair_value') if result_data else None,
            'graham_fair_value': result_data.get('graham_fair_value') if result_data else None,
            'average_fair_value': result_data.get('average_fair_value') if result_data else None,
            'saved_at': result_data.get('saved_at') if result_data else None,
            'upside_downside': None
        }
        
        # Calculate upside/downside if we have price and fair value
        if result_data and result_data.get('price') and result_data.get('dcf_fair_value'):
            price = result_data['price']
            dcf_fv = result_data['dcf_fair_value']
            upside = ((dcf_fv - price) / price) * 100
            stock_info['upside_downside'] = round(upside, 2)
        
        stocks.append(stock_info)
    
    return jsonify({
        'stocks': stocks,
        'total': len(stocks),
        'with_results': sum(1 for s in stocks if s['has_result']),
        'running': sum(1 for s in stocks if s['is_running'])
    })


@app.route('/api/stocks/<ticker>')
def get_stock_detail(ticker):
    """Get detailed information for a specific stock"""
    ticker = ticker.upper()
    result_file = results_dir / f'{ticker.lower()}_result.json'
    
    if not result_file.exists():
        return jsonify({'error': f'No result found for {ticker}'}), 404
    
    try:
        with open(result_file, 'r', encoding='utf-8') as f:
            result_data = json.load(f)
        
        # Load config
        config_file = config_dir / f'{ticker}.cfg'
        config_data = None
        if config_file.exists():
            import configparser
            config = configparser.ConfigParser()
            config.read(config_file)
            config_data = {section: dict(config[section]) for section in config.sections()}
        
        return jsonify({
            'ticker': ticker,
            'result': result_data,
            'config': config_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stocks/<ticker>/config')
def get_stock_config(ticker):
    """Get config for a specific stock"""
    ticker = ticker.upper()
    config_file = config_dir / f'{ticker}.cfg'
    
    if not config_file.exists():
        return jsonify({'error': f'Config file not found for {ticker}'}), 404
    
    try:
        import configparser
        config = configparser.ConfigParser()
        config.read(config_file)
        
        config_data = {}
        for section in config.sections():
            config_data[section] = dict(config[section])
        
        return jsonify({
            'ticker': ticker,
            'config': config_data,
            'config_file': str(config_file)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/status')
def get_status():
    """Get overall system status"""
    config_files = list(config_dir.glob('*.cfg'))
    result_files = list(results_dir.glob('*_result.json'))
    
    return jsonify({
        'total_stocks': len([f for f in config_files if f.stem.upper() != 'README']),
        'analyzed_stocks': len(result_files),
        'running_processes': len(running_processes),
        'running_tickers': list(running_processes.keys())
    })


@app.route('/api/stocks/<ticker>/run', methods=['POST'])
def run_analysis(ticker):
    """Trigger DCF analysis for a stock (async)"""
    ticker = ticker.upper()
    
    # Check if already running
    if ticker in running_processes:
        return jsonify({'error': f'Analysis already running for {ticker}'}), 400
    
    # Mark as running
    running_processes[ticker] = {
        'started_at': datetime.now().isoformat(),
        'status': 'running'
    }
    
    # TODO: Actually trigger the analysis in background
    # For now, just return success
    return jsonify({
        'message': f'Analysis started for {ticker}',
        'ticker': ticker,
        'status': 'running'
    })


@app.route('/api/stocks/<ticker>/status')
def get_stock_status(ticker):
    """Get running status for a stock"""
    ticker = ticker.upper()
    
    if ticker in running_processes:
        return jsonify({
            'ticker': ticker,
            'is_running': True,
            'status': running_processes[ticker]
        })
    
    # Check if result exists
    result_file = results_dir / f'{ticker.lower()}_result.json'
    if result_file.exists():
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                result_data = json.load(f)
            return jsonify({
                'ticker': ticker,
                'is_running': False,
                'has_result': True,
                'saved_at': result_data.get('saved_at')
            })
        except:
            pass
    
    return jsonify({
        'ticker': ticker,
        'is_running': False,
        'has_result': False
    })


if __name__ == '__main__':
    # Create necessary directories
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)
    
    print("=" * 80)
    print("DCF Analysis Web Service")
    print("=" * 80)
    print(f"Project root: {project_root}")
    print(f"Config dir: {config_dir}")
    print(f"Results dir: {results_dir}")
    print("=" * 80)
    print("\nStarting web server on http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)

