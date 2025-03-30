import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Any

from src.models.supabase import SupabaseDB
from src.utils.config_loader import load_config

logger = logging.getLogger(__name__)

def inspect_and_sync_figures(article_id: str) -> Dict[str, Any]:
    """
    Inspect and sync figures for a specific article.
    
    Args:
        article_id: The article ID
        
    Returns:
        Dict with inspection results
    """
    db = SupabaseDB()
    config = load_config()
    data_dir = Path(config.get('data_dir', 'data'))
    figures_dir = data_dir / article_id / "figures"
    
    results = {
        'article_id': article_id,
        'local_figures': [],
        'supabase_figures': [],
        'r2_urls': {},
        'subfigure_groups': {},
        'sync_results': []
    }
    
    # Check local figures directory
    logger.info(f"Inspecting figures for article {article_id}")
    logger.info(f"Local figures directory: {figures_dir}")
    
    if figures_dir.exists():
        # Find all figure files
        for fig_path in figures_dir.glob("*.png"):
            fig_id = fig_path.stem
            results['local_figures'].append(fig_id)
            
            # Check if it's a subfigure
            subfig_match = re.match(r'(fig\d+)_([a-z])', fig_id)
            if subfig_match:
                main_id = subfig_match.group(1)
                subfig_letter = subfig_match.group(2)
                
                if main_id not in results['subfigure_groups']:
                    results['subfigure_groups'][main_id] = set()
                results['subfigure_groups'][main_id].add(f"{subfig_letter}")
        
        logger.info(f"Found {len(results['local_figures'])} local figures")
        for main_id, subfigs in results['subfigure_groups'].items():
            logger.info(f"  Figure {main_id} has subfigures: {subfigs}")
    else:
        logger.warning(f"Local figures directory not found: {figures_dir}")
    
    # Check Supabase figures
    paper_figures = db.get_paper_figures(article_id)
    for fig in paper_figures:
        fig_id = fig.get('figure_id', '')
        results['supabase_figures'].append(fig_id)
        results['r2_urls'][fig_id] = fig.get('remote_path')
    
    logger.info(f"Found {len(results['supabase_figures'])} figures in Supabase")
    
    # Sync missing figures
    for fig_id in results['local_figures']:
        if fig_id not in results['supabase_figures']:
            logger.info(f"Syncing local figure to Supabase: {fig_id}")
            fig_path = figures_dir / f"{fig_id}.png"
            
            try:
                with open(fig_path, 'rb') as f:
                    image_data = f.read()
                
                # Get caption if available
                caption = ""
                meta_path = figures_dir / "figures.json"
                alt_meta_path = figures_dir / "figures_metadata.json"
                
                if meta_path.exists():
                    try:
                        with open(meta_path, 'r') as f:
                            figures_meta = json.load(f)
                            caption = figures_meta.get(fig_id, {}).get('caption', '')
                    except Exception as meta_err:
                        logger.warning(f"Error reading figures.json: {meta_err}")
                elif alt_meta_path.exists():
                    try:
                        with open(alt_meta_path, 'r') as f:
                            figures_meta = json.load(f)
                            caption = figures_meta.get(fig_id, {}).get('caption', '')
                    except Exception as meta_err:
                        logger.warning(f"Error reading figures_metadata.json: {meta_err}")
                
                # Add to Supabase/R2
                success = db.add_figure(article_id, fig_id, image_data, caption)
                results['sync_results'].append({
                    'figure_id': fig_id,
                    'success': success
                })
                
                if success:
                    # Get the URL
                    figure_url = db.get_figure_url(article_id, fig_id)
                    results['r2_urls'][fig_id] = figure_url
            except Exception as e:
                logger.error(f"Error syncing figure {fig_id}: {e}")
                results['sync_results'].append({
                    'figure_id': fig_id,
                    'success': False,
                    'error': str(e)
                })
    
    # Final check for figure 7 specifically (since you mentioned issues with it)
    logger.info("Specific check for figure 7...")
    
    # Check for main figure 7
    fig7_path = figures_dir / "fig7.png"
    fig7a_path = figures_dir / "fig7_a.png"
    fig7b_path = figures_dir / "fig7_b.png"
    
    logger.info(f"fig7.png exists: {fig7_path.exists()}")
    logger.info(f"fig7_a.png exists: {fig7a_path.exists()}")
    logger.info(f"fig7_b.png exists: {fig7b_path.exists()}")
    
    # Check R2 URLs
    fig7_url = db.get_figure_url(article_id, "fig7")
    fig7a_url = db.get_figure_url(article_id, "fig7_a")
    fig7b_url = db.get_figure_url(article_id, "fig7_b")
    
    logger.info(f"fig7 R2 URL: {fig7_url}")
    logger.info(f"fig7_a R2 URL: {fig7a_url}")
    logger.info(f"fig7_b R2 URL: {fig7b_url}")
    
    # Return detailed inspection results
    return results 