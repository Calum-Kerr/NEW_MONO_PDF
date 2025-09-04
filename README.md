# PDF Tools Monorepo

A comprehensive PDF tools platform with two branded sites:
- **snackpdf.com** → All-in-one PDF tools (iLovePDF clone)
- **revisepdf.com** → Live PDF editor (PDFfiller clone)

## 🏗️ Project Structure

```
├── snackpdf/          # Frontend for snackpdf.com (iLovePDF-style)
├── revisepdf/         # Frontend for revisepdf.com (live PDF editor)
├── api/               # Backend API (Python Flask)
├── supabase/          # Database schema and migrations
├── scripts/           # Development tools and deployment scripts
├── core/              # Shared utilities (auth, payments, file handling)
└── README.md          # This file
```

## 🚀 Tech Stack

- **Frontend**: HTML + Bootstrap 5.3 + Vanilla JavaScript
- **Backend**: Python Flask
- **Database**: Supabase (auth, database, storage)
- **Payments**: Stripe (subscriptions)
- **PDF Processing**: StirlingPDF integration
- **Hosting**: Heroku

## 📦 Setup Instructions

1. Clone the repository
2. Install dependencies (see individual folder READMEs)
3. Configure environment variables
4. Run database migrations
5. Start development servers

Detailed setup instructions are provided in each component's README file.