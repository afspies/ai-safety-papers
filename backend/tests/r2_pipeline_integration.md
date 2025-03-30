# Cloudflare R2 Pipeline Integration

## Overview
This document outlines the integration of Cloudflare R2 storage into the AI Safety Papers pipeline. The integration has been designed to use Cloudflare R2 for storing and serving figure images extracted from papers, while still maintaining compatibility with local storage for graceful degradation.

The system now uses a public URL format for all figures stored in R2 (e.g., `https://assets.afspies.com/figures/paper_id/fig1.png`), which provides a clean and consistent way to access images in the frontend.

## Components Implemented

1. **`CloudflareR2Client` in `src/utils/cloudflare_r2.py`**:
   - Fully implemented S3-compatible API client for Cloudflare R2
   - Supports upload, download, delete, and presigned URL generation
   - Uses long-term caching headers (1 year) for performance

2. **`SupabaseDB` Extensions in `src/models/supabase.py`**:
   - Added methods for adding, retrieving, and listing figures
   - Supports batch uploads for better performance
   - Includes fallback mechanisms to local storage

3. **`figure_processor.py` Updates**:
   - Modified to support both local and R2 storage
   - Uploads figures in batch mode for better performance
   - Maintains backward compatibility

4. **Database Schema**:
   - Added tables for `paper_figures` and `paper_summaries`
   - Created indexes for optimized queries

5. **Testing Tools**:
   - Created lightweight test scripts for isolated testing
   - Added integration tests for full pipeline

## Setup Requirements

1. **Create Cloudflare R2 Bucket**:
   - Name: `ai-safety-papers`
   - Configure CORS settings to allow public access

2. **Configure API Keys**:
   - Set environment variables or update config:
     ```
     R2_ACCOUNT_ID=your_cloudflare_account_id
     R2_ACCESS_KEY_ID=your_r2_access_key_id
     R2_ACCESS_KEY_SECRET=your_r2_access_key_secret
     R2_BUCKET=ai-safety-papers
     R2_PUBLIC_URL_PREFIX=https://assets.afspies.com/figures
     ```

3. **Update Configuration**:
   - Ensure `cloudflare_r2.enabled` is set to `true` in `config.yaml`

## Storage Structure

- Figures are stored under `figures/{paper_id}/{figure_id}.png`
- Thumbnails are stored under `figures/{paper_id}/thumbnail_full.png` and `figures/{paper_id}/thumbnail_abstract.png`
- Metadata is stored in Supabase with references to R2 URLs

## Implementation Details

1. **Figure Extraction and Upload**:
   - Images are uploaded with proper MIME types and cache headers
   - Batch uploads for better performance
   - Locally cached with fallback mechanism

2. **API Integration**:
   - API endpoints serve public URLs (https://assets.afspies.com/figures/paper_id/figure_id.png)
   - Clean, consistent URLs for frontend integration
   - Fallback to presigned URLs for private resources when needed

3. **Migration**:
   - The `migrate_to_r2.py` script transfers existing data to R2
   - Incremental migration supported - only uploads missing files

## Next Steps

1. **Set up Supabase Database**:
   - Create required tables using `create_db_tables.sql`
   - Set environment variables for Supabase connection

2. **Test Full Pipeline**:
   - Run `test_r2_integration.py` to verify basic functionality
   - Process a few test papers with `run_processing.py`

3. **Monitor and Optimize**:
   - Add monitoring for R2 usage and costs
   - Optimize cache settings and CDN integration