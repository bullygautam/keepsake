KEEPSAKE STUDIO 5.2 — WINDOWS INSTALLER BUILD PROJECT

This ZIP is the BUILD PROJECT, not an installer. A Windows .exe has NOT been compiled or tested here.

FOR A NON-PROGRAMMER:
1. Create a free GitHub account if needed.
2. Create a PRIVATE GitHub repository (e.g. keepsake-studio).
3. Upload the contents of this folder to the repository, including the hidden .github folder.
   You can use GitHub Desktop to upload the folder, or GitHub's Add file > Upload files.
4. Open the repository's Actions tab and select "Build Windows installer".
5. Choose Run workflow (or let the workflow run after pushing to main).
6. Wait for the Windows job to finish. Download the "KeepsakeStudio-Windows-Installer" artifact.
7. Extract that downloaded artifact and run KeepsakeStudio_Setup_5_2.exe on Windows.

This build uses Python 3.12 INSIDE GitHub's Windows build machine; it does not require
Python to be installed on your PC. It packages the small u2netp AI cutout model.
Internet is needed during the BUILD, not for the model at runtime.

LIMITATIONS:
- Windows installer has not been compiled or GUI-tested in this environment.
- Automatic cutout quality varies. This app still uses a template-based collage engine.
- This installer is unsigned, so Windows SmartScreen may warn on first run.
- GitHub Actions may have usage limits and account requirements.
- Do not upload personal photos to GitHub; the repository only needs application source.
