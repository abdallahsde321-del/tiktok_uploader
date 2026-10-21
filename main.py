import os
import subprocess
from googleapiclient.discovery import build
import yt_dlp

# ================= الإعدادات =================
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
YOUTUBE_CHANNEL_ID = "UC04ZxFjp6c-6QeReK4JVcjQ"
UPLOADS_PLAYLIST_ID = YOUTUBE_CHANNEL_ID.replace("UC", "UU", 1)

HISTORY_FILE = "history.txt"
VIDEO_FILENAME = "video_to_upload.mp4"
# =============================================

def get_downloaded_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return f.read().splitlines()

def save_to_history(video_id):
    with open(HISTORY_FILE, "a") as f:
        f.write(video_id + "\n")

def get_unuploaded_videos(history):
    """جلب آخر 50 فيديو من القناة والبحث عن فيديو لم يتم رفعه"""
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    
    request = youtube.playlistItems().list(
        part="snippet",
        playlistId=UPLOADS_PLAYLIST_ID,
        maxResults=50
    )
    response = request.execute()
    
    if not response.get("items"):
        return None, None

    # البحث من الأقدم للأحدث في آخر 50 فيديو
    items = reversed(response["items"]) 
    
    for item in items:
        video_id = item["snippet"]["resourceId"]["videoId"]
        title = item["snippet"]["title"]
        
        if video_id not in history:
            return video_id, title
            
    return None, None

def download_short(video_id):
    """تحميل الفيديو مع التأكد من أنه شورتس (أقل من 65 ثانية)"""
    print(f"[DOWNLOAD] جاري فحص وتحميل الفيديو: {video_id}...")
    ydl_opts = {
        'outtmpl': VIDEO_FILENAME,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'match_filter': yt_dlp.utils.match_filter_func("duration <= 65"),
        'quiet': False
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
        
        if os.path.exists(VIDEO_FILENAME):
            return True
        return False
    except Exception as e:
        print(f"[ERROR] خطأ في التحميل (قد يكون فيديو طويل وليس شورتس): {e}")
        return False

def upload_to_tiktok(video_path, title):
    print(f"[UPLOAD] جاري الرفع إلى تيك توك: {title}...")
    command = [
        "tiktok-uploader",
        "-v", video_path,
        "-d", f"{title} #shorts #fyp",
        "-c", "cookies.txt"
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        print("[UPLOAD] تم الرفع بنجاح!")
        return True
    else:
        print(f"[ERROR] فشل الرفع: {result.stderr}")
        return False

def main():
    if not YOUTUBE_API_KEY:
        print("[FATAL] YOUTUBE_API_KEY is not set.")
        return

    history = get_downloaded_history()
    video_id, title = get_unuploaded_videos(history)
    
    if not video_id:
        print("لا يوجد فيديوهات جديدة لرفعها.")
        return
        
    print(f"تم العثور على فيديو جديد! المعرف: {video_id} | العنوان: {title}")
    
    is_downloaded = download_short(video_id)
    
    if is_downloaded:
        success = upload_to_tiktok(VIDEO_FILENAME, title)
        if success:
            save_to_history(video_id)
            os.remove(VIDEO_FILENAME)
            print(f"[CLEANUP] تم رفع وحذف الفيديو {VIDEO_FILENAME} وتحديث السجل.")
    else:
        print("[SKIP] تم تخطي الفيديو (ربما ليس شورتس). تسجيله لتجاهله مستقبلاً.")
        save_to_history(video_id)

if __name__ == "__main__":
    main()
