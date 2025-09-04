# RevisePDF Frontend

This directory contains the frontend application for RevisePDF.com - a PDFfiller-style live PDF editor for professional document editing.

## Features

- **Live PDF Editing**: In-browser PDF editing with real-time preview
- **Professional Interface**: PDFfiller-style layout with toolbar and sidebar
- **Multiple Tool Types**: Text, signature, annotation, and drawing tools
- **PDF Viewing**: Built-in PDF viewer using PDF.js
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Collaboration**: Foundation for multi-user editing

## Editing Tools

1. **Text Tool** - Add custom text with font size and color options
2. **Signature Tool** - Create and insert digital signatures (draw or type)
3. **Highlight Tool** - Highlight text and add annotations
4. **Drawing Tool** - Freehand drawing and shapes
5. **Image Tool** - Insert logos and images into documents
6. **Form Filling** - Fill out PDF forms and fields

## File Structure

```
revisepdf/
├── index.html          # Main editor interface
├── css/
│   └── editor.css      # Editor-specific styles
├── js/
│   ├── editor.js       # Main editor functionality
│   ├── pdf-viewer.js   # PDF viewing and rendering
│   └── annotations.js  # Annotation and editing tools
└── images/            # Static images and assets
```

## Development

To run the frontend locally:

```bash
cd revisepdf
python3 -m http.server 3001
```

Then open http://localhost:3001 in your browser.

## Editor Interface

### Welcome Screen
- Professional landing page with feature highlights
- Drag-and-drop PDF upload area
- Feature grid showing editing capabilities

### Editor Mode
- **Toolbar**: Zoom controls and editing tools
- **Sidebar**: Page thumbnails and navigation
- **Main Area**: PDF viewer with annotation layer
- **Modals**: Tool-specific configuration dialogs

## PDF.js Integration

Uses PDF.js library for:
- PDF rendering and display
- Page navigation
- Zoom functionality
- Text extraction for forms

## Annotation System

Built-in annotation system supporting:
- Text annotations with custom styling
- Signature annotations (drawn or typed)
- Highlight annotations
- Drawing annotations
- Moveable and resizable elements

## API Integration

Integrates with the backend API for:
- User authentication
- PDF upload and storage
- Document saving and export
- Collaborative editing features

## Styling

Professional interface styling with:
- Dark blue header matching PDFfiller
- Clean tool buttons and icons
- Smooth animations and transitions
- Responsive layout for all screen sizes
- Custom scrollbars and UI elements

## Browser Compatibility

Supports modern browsers with:
- HTML5 Canvas for drawing
- File API for uploads
- CSS3 for animations
- ES6+ JavaScript features