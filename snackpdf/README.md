# SnackPDF Frontend

This directory contains the frontend application for SnackPDF.com - an iLovePDF-style all-in-one PDF tools website.

## Features

- **Tool Grid Layout**: Clean, organized display of PDF tools similar to iLovePDF
- **Drag & Drop Upload**: Intuitive file upload with drag-and-drop support
- **Responsive Design**: Mobile-friendly interface using Bootstrap 5.3
- **Authentication**: Complete login/register system with modal interfaces
- **Real-time Processing**: Progress indicators and status updates
- **SEO Optimized**: Comprehensive meta tags and structured data

## Tools Available

1. **Merge PDF** - Combine multiple PDF files into one document
2. **Split PDF** - Extract pages or split PDF into separate files
3. **Compress PDF** - Reduce file size while maintaining quality
4. **Convert to PDF** - Convert Word, Excel, PowerPoint, images to PDF
5. **Extract Pages** - Extract specific pages from documents
6. **Rotate PDF** - Rotate pages in PDF documents

## File Structure

```
snackpdf/
├── index.html          # Main homepage
├── css/
│   └── style.css       # Custom styles and Bootstrap overrides
├── js/
│   └── app.js         # Frontend JavaScript and API integration
└── images/            # Static images and assets
```

## Development

To run the frontend locally:

```bash
cd snackpdf
python3 -m http.server 3000
```

Then open http://localhost:3000 in your browser.

## API Integration

The frontend integrates with the Flask API backend running on port 5000. Key API endpoints used:

- `POST /api/auth/login` - User authentication
- `POST /api/auth/register` - User registration
- `POST /api/files/upload` - File upload
- `POST /api/pdf/merge` - PDF merging
- `POST /api/pdf/split` - PDF splitting

## Styling

Uses Bootstrap 5.3 with custom CSS for:
- Tool cards with hover animations
- File upload areas with drag-and-drop styling
- Modal dialogs for authentication
- Responsive grid layouts
- Custom color scheme and branding

## SEO Features

- Comprehensive meta tags for search engines
- Open Graph tags for social media
- Twitter Card metadata
- Structured data (JSON-LD) for rich snippets
- Semantic HTML with proper heading hierarchy