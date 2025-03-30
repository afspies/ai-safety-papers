# Cloudflare R2 Integration for AI Safety Papers

## Overview

This document provides an overview of the Cloudflare R2 integration for the AI Safety Papers project. The integration enables storing figure images extracted from papers in Cloudflare R2, a scalable object storage service, which provides better performance, reliability, and scalability compared to local file storage.

The system now uses a public URL format for all figures stored in R2 (e.g., `https://assets.afspies.com/figures/paper_id/fig1.png`), which provides a clean and consistent way to access images for the frontend.

## Integration Status

✅ **Core Implementation**: Complete  
✅ **Testing Tools**: Complete  
✅ **Figure Processing Integration**: Complete  
✅ **API Integration**: Complete  
⚠️ **Supabase Integration**: Configuration required  
⚠️ **Migration Script**: Requires Supabase credentials  

## Components

### 1. CloudflareR2Client

A flexible client for interacting with Cloudflare R2 storage, implemented in `src/utils/cloudflare_r2.py`. The client provides the following functionality:

- **Upload files** with proper MIME types and cache headers (1 year for immutable content)
- **Generate public URLs** using the configured prefix (e.g., `https://assets.afspies.com/figures/paper_id/fig1.png`)
- **Download files** with error handling and retries
- **Delete files** for cleanup operations
- **Generate presigned URLs** for temporary access to private files

### 2. SupabaseDB Enhancements

Extension to the `SupabaseDB` class in `src/models/supabase.py` to handle figure storage and metadata:

- **Store and retrieve public figure URLs** in Supabase tables
- **Batch upload multiple figures** for better performance
- **Consistent URL format** for frontend integration
- **Fallback to local storage** when R2 is unavailable or misconfigured

### 3. Figure Processor Updates

Enhanced `figure_processor.py` to support R2 integration:

- **Upload figures during extraction** for seamless integration
- **Create R2-aware thumbnails** for use in the frontend
- **Maintain backward compatibility** with local storage

### 4. Database Schema

New tables for storing figure metadata:

- **`paper_figures`**: Stores figure metadata and R2 URLs
- **`paper_summaries`**: Stores paper summaries with display figure information

## Setup Instructions

### Prerequisites

1. A Cloudflare account with R2 access
2. A Supabase project for metadata storage
3. Proper API keys and credentials

### Configuration

1. **Set environment variables or update config.yaml**:
   ```yaml
   cloudflare_r2:
     enabled: true
     account_id: "your_account_id"
     access_key_id: "your_access_key_id"
     access_key_secret: "your_access_key_secret"
     bucket_name: "ai-safety-papers"
     public_url_prefix: "https://assets.afspies.com/figures"
   ```

2. **Create the required Supabase tables**:
   - Run the SQL in `create_db_tables.sql` in your Supabase SQL editor

3. **Set Supabase environment variables**:
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```

### Testing the Integration

1. **Basic R2 functionality test**:
   ```
   python test_r2_integration.py
   ```

2. **Figure upload test**:
   ```
   python test_r2_figures_direct.py --auto
   ```

3. **View uploaded figures**:
   ```
   python view_r2_figure.py --paper-id <paper_id> --figure-id <figure_id>
   ```

### Data Migration

1. **Migrate existing data to R2**:
   ```
   python migrate_to_r2.py
   ```

## Architecture

### Storage Structure

- **R2 Storage Keys**: `figures/{paper_id}/{figure_id}.png`
- **Public URLs**: `https://assets.afspies.com/figures/{paper_id}/{figure_id}.png`
- **Thumbnails**: `figures/{paper_id}/thumbnail_{mode}.png`
- **Metadata**: Stored in Supabase tables with references to public URLs

### Fallback Mechanism

When R2 is unavailable or a figure is not found in R2:

1. The system attempts to retrieve the figure from local storage
2. If found locally, it uploads the figure to R2 for future requests
3. In case of complete failure, it serves the figure from local storage

## Performance Considerations

- **Public URLs**: Clean, consistent URLs for frontend integration
- **Cache Headers**: Long-term caching (1 year) for immutable content
- **Batch Operations**: Figures are uploaded in batches for better performance
- **Lazy Loading**: Figures are only uploaded to R2 when needed
- **CDN Integration**: Public URLs can be served via Cloudflare's CDN for better performance

## Monitoring and Maintenance

- **Logs**: Check logs for errors and performance issues
- **Costs**: Monitor R2 usage and costs in Cloudflare dashboard
- **Cleanup**: Run cleanup scripts regularly to remove unused figures

## Troubleshooting

### Common Issues

1. **Permission Errors**:
   - Verify your R2 credentials are correctly configured
   - Check access permissions for the R2 bucket

2. **Missing Figures**:
   - Verify the figure exists in local storage
   - Check the R2 key format (figures/{paper_id}/{figure_id}.png)

3. **Supabase Integration Issues**:
   - Verify Supabase credentials
   - Ensure the required tables exist in your Supabase project

### Diagnostic Tools

- **test_r2_integration.py**: Tests basic R2 functionality
- **test_r2_figures_direct.py**: Tests figure upload functionality
- **view_r2_figure.py**: Views figures stored in R2

## Next Steps

1. **DNS & CDN Setup**: Set up DNS for the custom domain (assets.afspies.com)
2. **Cloudflare Worker**: Configure a Worker to serve R2 objects via the custom domain
3. **Supabase Integration**: Complete setup of Supabase project
4. **Migration Script**: Run the migration script to transfer existing data
5. **API Testing**: Test the API endpoints with public URLs
6. **Monitoring**: Set up monitoring for R2 usage and costs

## Additional Resources

- [Cloudflare R2 Documentation](https://developers.cloudflare.com/r2/)
- [Supabase Documentation](https://supabase.io/docs)
- [boto3 S3 Client Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)