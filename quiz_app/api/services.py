'''Service layer for Quiz generation: yt-dlp → Whisper → Gemini.

Responsibilities:
- Normalize and validate YouTube URLs.
- Check video availability and (optionally) max duration.
- Download audio with yt-dlp.
- Ensure FFmpeg is available and transcribe audio with Whisper.
- Build a strict LLM prompt and call Gemini to generate a quiz.
- Validate the returned quiz JSON and persist Quiz/Question models.

Error handling contract:
- Expected, user-facing problems (invalid URL, unavailable video, missing FFmpeg,
  missing GEMINI_API_KEY, invalid LLM JSON, etc.) raise ValueError with a clear
  message. The API view maps ValueError → HTTP 400.
- Unexpected failures bubble up as generic exceptions (HTTP 500 in the view).

Dependencies:
- yt-dlp, FFmpeg (binary on PATH), whisper (OpenAI Whisper), google-genai (Gemini).
'''

import json, os, re, tempfile, contextlib, pathlib, shutil
import yt_dlp
import whisper

from django.conf import settings
from google import genai
from yt_dlp.utils import DownloadError, ExtractorError

YOUTUBE_CANONICAL = 'https://www.youtube.com/watch?v={vid}'

def extract_youtube_id(url: str) -> str:
    '''Extract a YouTube video ID from common URL forms.

    Supports:
      - https://www.youtube.com/watch?v=<id>
      - https://youtu.be/<id>
      - https://www.youtube.com/embed/<id>

    Args:
        url: The input URL string.

    Returns:
        The 11-character YouTube video ID.

    Raises:
        ValueError: If the URL is unsupported or no ID can be extracted.
    '''

    if not url or 'youtube' not in url and 'youtu.be' not in url:
        raise ValueError('Unsupported URL.')
    
    m = re.search(r"[?&]v=([A-Za-z0-9_-]{11})", url)
    if m: return m.group(1)

    m = re.search(r"(youtu\.be/|embed/)([A-Za-z0-9_-]{11})", url)
    if m: return m.group(2)

    raise ValueError('Could not extract YouTube video id.')

def ensure_video_available(url: str, max_duration_sec: int | None = None):
    '''Check if a YouTube video is available and optionally enforce a max duration.

    Args:
        url: Canonical YouTube watch URL.
        max_duration_sec: Optional maximum allowed duration in seconds.

    Returns:
        The yt-dlp info dict (metadata) for the video.

    Raises:
        ValueError: If the video is unavailable/invalid or exceeds the duration limit.
    '''

    try:
        with yt_dlp.YoutubeDL({'quiet': True, 'noplaylist': True}) as ydl:
            info = ydl.extract_info(url, download=False)
        if max_duration_sec and info.get('duration') and info['duration'] > max_duration_sec:
            raise ValueError('Video too long.')
        return info
    except (DownloadError, ExtractorError):
        raise ValueError('YouTube video unavailable or invalid.')

def download_audio(url: str) -> str:
    '''Download best-available audio stream for a YouTube video.

    Args:
        url: Any YouTube URL containing a valid video ID (normalized internally).

    Returns:
        Absolute file path to the downloaded audio file.

    Raises:
        ValueError: If the download fails or no file is produced.
    '''

    try:
        vid = extract_youtube_id(url)
        outtmpl = str((getattr(settings, 'QUIZ_TMP_DIR', pathlib.Path(tempfile.gettempdir())) / f"{vid}.%(ext)s").resolve())
        ydl_opts = {
            'format': "bestaudio/best",
            'outtmpl': outtmpl,
            'quiet': True,
            'noplaylist': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(YOUTUBE_CANONICAL.format(vid=vid), download=True)
            path = ydl.prepare_filename(info)
        if not path or not os.path.exists(path):
            raise ValueError('Audio download failed.')
        return path
    except (DownloadError, ExtractorError) as e:
        raise ValueError('Failed to download audio from Youtube.')

def _require_ffmpeg():
    '''Ensure FFmpeg is available on PATH; attempt to extend PATH from settings.'''

    ff = shutil.which('ffmpeg')
    if not ff and getattr(settings, 'FFMPEG_DIR', None):
        os.environ['PATH'] = settings.FFMPEG_DIR + os.pathsep + os.environ.get('PATH', '')
        ff = shutil.which('ffmpeg')
    if not ff:
        raise ValueError('FFmpeg not found. Please install FFmpeg and add it to PATH.')
    return ff

def transcribe_audio(audio_path: str) -> str:
    '''Transcribe an audio file to text using Whisper.

    Args:
        audio_path: Path to the downloaded audio file.

    Returns:
        The transcribed text (stripped).

    Raises:
        ValueError: If FFmpeg is missing or transcription fails.
    '''

    _require_ffmpeg()
    model_name = getattr(settings, 'WHISPER_MODEL', 'small')
    try:
        import whisper
        model = whisper.load_model(model_name)
        result = model.transcribe(audio_path)
        return result.get('text', '').strip()
    except FileNotFoundError as e:
        if 'ffmpeg' in str(e).lower():
            raise ValueError('FFmpeg is not installed or not on PATH.')
        raise
    except Exception as e:
        raise ValueError(f"Transcription failed: {e}")

def build_quiz_prompt(transcript: str, num_questions: int = 10) -> str:
    '''Construct a strict prompt instructing Gemini to return valid JSON only.'''

    return f"""
Based on the following transcript, generate a quiz in valid JSON format.

The quiz must follow this exact structure:

{{
  "title": "Create a concise quiz title based on the topic of the transcript.",
  "description": "Summarize the transcript in no more than 150 characters. Do not include any quiz questions or answers.",
  "questions": [
    {{
      "question_title": "The question goes here.",
      "question_options": ["Option A", "Option B", "Option C", "Option D"],
      "answer": "The correct answer from the above options"
    }}
    // repeat until exactly {num_questions} questions in total
  ]
}}

Requirements:
- Each question must have exactly 4 distinct answer options.
- Only one correct answer per question, and it must be present in "question_options".
- The output must be valid JSON and parsable as-is. Do NOT include markdown fences or explanations.

Transcript:
\"\"\"{transcript}\"\"\"
""".strip()

def generate_quiz_with_gemini(transcript: str, num_questions: int = 10) -> dict:
    '''Call Gemini to generate a quiz JSON and parse/validate the result.

    Args:
        transcript: The transcribed text.
        num_questions: Number of questions to request and enforce.

    Returns:
        A Python dict with keys: title, description, questions[list].

    Raises:
        ValueError: If GEMINI_API_KEY is missing, the call fails, or the JSON is invalid.
    '''

    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not api_key:
        raise ValueError('GEMINI_API_KEY is not configured.')
    client = genai.Client(api_key=api_key)
    try:
        resp = client.models.generate_content(model='gemini-2.5-flash', contents=build_quiz_prompt(transcript, num_questions))
    except Exception as e:
        raise ValueError(f"Gemini request failed: {e}")
    
    text = getattr(resp, 'text', None) or getattr(resp, 'candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
    
    json_str = text.strip()
    
    if "```" in json_str:
        json_str = json_str.split("```")[1]
        
        json_str = "\n".join([l for l in json_str.splitlines() if l.strip().lower() != 'json'])
    
    if not json_str.strip().startswith('{'):
        s = json_str.find('{')
        e = json_str.rfind('}')
        json_str = json_str[s:e+1]
    data = json.loads(json_str)
    validate_quiz_dict(data, num_questions=num_questions)
    return data

def validate_quiz_dict(d: dict, num_questions: int = 10):
    '''Validate the shape and constraints of the generated quiz JSON.'''

    if not isinstance(d, dict):
        raise ValueError('Quiz must be a JSON object.')
    if "title" not in d or 'description' not in d or 'questions' not in d:
        raise ValueError('Quiz JSON must contain title, description, questions.')
    qs = d['questions']
    if not isinstance(qs, list) or len(qs) != num_questions:
        raise ValueError(f"Quiz must contain exactly {num_questions} questions.")
    for q in qs:
        if not all(k in q for k in ('question_title', 'question_options', 'answer')):
            raise ValueError('Each question must have question_title, question_options, answer.')
        opts = q['question_options']
        if not isinstance(opts, list) or len(opts) != 4 or len(set(opts)) != 4:
            raise ValueError('Each question must have exactly 4 distinct options.')
        if q['answer'] not in opts:
            raise ValueError('Answer must be one of question_options.')

def create_quiz_from_youtube(url: str, owner, num_questions: int = 10):
    '''End-to-end pipeline: validate → download → transcribe → LLM → persist.

    Args:
        url: Any YouTube URL containing a valid video ID.
        owner: The Django User who will own the quiz.
        num_questions: Number of questions to generate and enforce.

    Returns:
        The created Quiz instance (with related Questions saved).

    Raises:
        ValueError: For expected failure modes (invalid URL, video unavailable,
        FFmpeg missing, LLM errors, invalid JSON, etc.).
    '''

    canonical_url = YOUTUBE_CANONICAL.format(vid=extract_youtube_id(url))
    ensure_video_available(canonical_url, max_duration_sec=getattr(settings, 'QUIZ_MAX_DURATION_SEC', None))    
    audio_path = download_audio(canonical_url)
    try:
        transcript = transcribe_audio(audio_path)
    finally:
        with contextlib.suppress(Exception):
            pathlib.Path(audio_path).unlink(missing_ok=True)

    quiz_dict = generate_quiz_with_gemini(transcript, num_questions=num_questions)

    from ..models import Quiz, Question
    quiz = Quiz.objects.create(
        owner=owner,
        title=quiz_dict['title'],
        description=quiz_dict['description'],
        video_url=canonical_url,
    )
    questions = [
        Question(
            quiz=quiz,
            question_title=q['question_title'],
            question_options=q['question_options'],
            answer=q['answer'],
        ) for q in quiz_dict['questions']
    ]
    Question.objects.bulk_create(questions)
    return quiz