Quizly Backend

![Quizly Logo](logoheader.png)

This repository contains the Django REST Framework–based backend for **Quizly**, a quiz app that takes a YouTube URL, extracts the audio with `yt-dlp`, transcribes it with Whisper, and asks Gemini to generate a multiple-choice quiz. Auth is cookie-based JWT.

---

## Getting Started

### Backend Setup

1. **Create a virtuel environment**
    ```bash
    python3 -m venv env
    ```
    ```bash
    source env/bin/activate   # macOS/Linux
    ```
    ### or
    ```bash
    .\env\Scripts\Activate.ps1  # Windows PowerShell
    ```

2. **Install Python dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3. **Create a Gemini API key and configure environment**
   - Go to **Google AI Studio** and create an API key (Gemini).
   - Create a file named **`.env`** in the project root (next to `manage.py`) and add:
     ```
     DEBUG=True
     SECRET_KEY=change-me-for-prod
     GEMINI_API_KEY=YOUR_GOOGLE_GEMINI_API_KEY
     # Optional cookie settings (for production / cross-site setups)
     # COOKIE_SAMESITE=Lax        # or None (requires HTTPS)
     # COOKIE_DOMAIN=.yourdomain.com
     # Optional if FFmpeg is not on PATH:
     # FFMPEG_DIR=/usr/bin
     # FFMPEG_DIR=C:\ffmpeg\bin
     ```
   > The project loads `.env` automatically on startup.  
   > Alternatively, you can export `GEMINI_API_KEY` via your shell or hosting platform’s env settings.

4. **Install FFmpeg (required by Whisper/yt-dlp)**

    - **macOS (Homebrew)**: `brew install ffmpeg`
    - **Linux (Debian/Ubuntu)**: `sudo apt-get update && sudo apt-get install -y ffmpeg`
    - **Windows**: download a static build (e.g. gyan.dev), extract to `C:\ffmpeg`, and add `C:\ffmpeg\bin` to your `PATH`.

5. **Apply database migrations**
    ```bash
    python manage.py makemigrations
    ```
    ```bash
    python manage.py migrate
    ```

6. **Optional: Create a superuser**
    ```bash
    python manage.py createsuperuser
    ```

7. **Run the backend server**
    ```bash
    python manage.py runserver
    ```

    The API will be available at "http://127.0.0.1:8000"

---

### Frontend Setup ("https://github.com/Sessa89/Quizly_Frontend")

1. **Open the frontend folder**  
    In your code editor (e.g., VS Code), open the frontend directory.

2. **Start a local static server**
    - Right-click on index.html (inside frontend) and select "Open with Live Server" if you have VS Code Live Server installed
    - The frontend will run at "http://127.0.0.1:5500/"

---

## Features

- **Authentication (cookie-based JWT)**
    - Register with username + email + password (password policy ≥ 6 characters)
    - Login → sets `access_token` and `refresh_token` as **HttpOnly** cookies
    - Token refresh via cookie (reads `refresh_token` and sets a new `access_token`)
    - Logout (blacklists refresh token and deletes cookies)
    - Custom `CookieJWTAuthentication` so protected endpoints work with cookies out of the box

- **Quiz Generation**
    - `yt-dlp` downloads audio from a YouTube URL
    - Whisper transcribes audio to text
    - Gemini generates **exactly 10** questions (each with 4 distinct options and one correct answer)
    - All data stored in the database (Quiz + Questions)

- **Admin Panel**
    - Manage Quizzes with inline Questions (validation ensures exactly 4 options and a valid answer)
    - User admin with SimpleJWT blacklist integration (view/blacklist tokens)

---