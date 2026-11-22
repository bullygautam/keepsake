KEEPSAKE STUDIO 5 — LOCAL FIRST

1. Install Python 3.11 or 3.12 from python.org (check Add Python to PATH).
2. Double-click START_WINDOWS.bat. It installs Pillow if missing.
3. Import a photo folder or individual files.
4. The app sorts imported photographs by camera EXIF date when available.
5. Browse 14 photos per two-page spread, remix, save a .keepsake album, export HD PNG/PDF.

OPTIONAL CUTOUTS (EXPERIMENTAL)
Run INSTALL_AI_CUTOUTS_WINDOWS.bat, restart the app, then check "AI subject stickers".
The first use downloads a neural model; later inference is local. Processing may be slow
on CPU. This feature works best on photos with one prominent person; some cutouts fail.

NOTES
- JPG/PNG/WebP are recommended; HEIC may need extra system support.
- This is an evolving desktop prototype, not a signed Windows installer.
- No photos are uploaded by the core app. Optional cutout model is downloaded once.
- AI cutouts require compatible Python packages and can fail on some Windows setups.
- Do not delete the originals until your saved album has been reopened successfully.
