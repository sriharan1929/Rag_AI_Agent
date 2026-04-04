# TODO: Add Support for All File Formats

## Plan:
- [x] 1. Create TODO.md file for tracking
- [x] 2. Update backend/main.py:
  - [x] Update `/upload/` endpoint to accept all file formats
  - [x] Update `create_vector_db()` to handle Word, Excel files
  - [x] Add support for multiple file uploads
  - [x] Keep ZIP extraction functionality
- [ ] 3. Update frontend/App.js:
  - [ ] Update file input accept attribute
  - [ ] Update UI labels

## Required Python packages:
- python-docx (for Word files)
- openpyxl (for Excel files)
- unstructured (for various document formats)
