import os
import subprocess
from googleapiclient.discovery import build
import yt_dlp
from datetime import datetime, timedelta

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

def get_unuploaded_videos(history, max_videos=180):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    
    request = youtube.playlistItems().list(
        part="snippet",
        playlistId=UPLOADS_PLAYLIST_ID,
        maxResults=50
    )
    response = request.execute()
    
    if not response.get("items"):
        return []

    items = reversed(response["items"]) 
    new_videos = []
    
    for item in items:
        video_id = item["snippet"]["resourceId"]["videoId"]
        title = item["snippet"]["title"]
        
        if video_id not in history:
            new_videos.append({"id": video_id, "title": title})
            if len(new_videos) >= max_videos:
                break
                
    return new_videos

def download_video(video_id):
    print(f"[DOWNLOAD] جاري تحميل الفيديو: {video_id}...")
    ydl_opts = {
        'outtmpl': VIDEO_FILENAME,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'js_runtimes': {'deno': {}, 'node': {}},
        'quiet': False
    }
    
    # تفعيل ملف كوكيز يوتيوب لتجاوز حماية الروبوتات نهائياً
    if os.path.exists("youtube_cookies.txt") and os.path.getsize("youtube_cookies.txt") > 0:
        ydl_opts['cookiefile'] = 'youtube_cookies.txt'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
        
        if os.path.exists(VIDEO_FILENAME):
            return True
        return False
    except Exception as e:
        print(f"[ERROR] خطأ في التحميل: {e}")
        return False

def upload_to_tiktok(video_path, title, schedule_time=None):
    print(f"[UPLOAD] جاري الرفع إلى تيك توك: {title}...")
    command = [
        "tiktok-uploader",
        "-v", video_path,
        "-d", title,
        "-c", "cookies.txt"
    ]
    
    if schedule_time:
        formatted_time = schedule_time.strftime("%Y-%m-%d %H:%M")
        command.extend(["-s", formatted_time])
        print(f"[SCHEDULE] تم جدولة الفيديو ليُنشر في: {formatted_time}")
    else:
        print(f"[PUBLIC] سيتم نشر الفيديو للعامة فوراً.")

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        print("[UPLOAD] تم الرفع والجدولة بنجاح!")
        return True
    else:
        print(f"[ERROR] فشل الرفع: {result.stderr}")
        return False

def main():
    if not YOUTUBE_API_KEY:
        print("[FATAL] YOUTUBE_API_KEY is not set.")
        return

    history = get_downloaded_history()
    videos_to_upload = get_unuploaded_videos(history, max_videos=180)
    
    if not videos_to_upload:
        print("لا يوجد فيديوهات جديدة لرفعها.")
        return
        
    print(f"تم العثور على {len(videos_to_upload)} فيديو. البدء في معالجتها وجدولتها...")
    
    now = datetime.now()
    
    for index, vid in enumerate(videos_to_upload):
        v_id = vid["id"]
        title = vid["title"]
        
        print(f"\n--- معالجة الفيديو ({index + 1}/{len(videos_to_upload)}): {title} ({v_id}) ---")
        
        is_downloaded = download_video(v_id)
        
        if is_downloaded:
            if index == 0:
                schedule_time = None 
            else:
                schedule_time = now + timedelta(hours=4 * index)
                
            success = upload_to_tiktok(VIDEO_FILENAME, title, schedule_time)
            
            if success:
                save_to_history(v_id)
                os.remove(VIDEO_FILENAME)
                print(f"[CLEANUP] تم حذف الفيديو {VIDEO_FILENAME} من الخادم.")
            else:
                print(f"[WARN] فشل رفع {v_id}. تسجيله لتخطيه.")
                save_to_history(v_id)
                if os.path.exists(VIDEO_FILENAME):
                    os.remove(VIDEO_FILENAME)
        else:
            print(f"[SKIP] تخطي الفيديو {v_id} بسبب فشل التحميل.")
            save_to_history(v_id)

    print(f"\n=== انتهت العملية بنجاح! ===")

if __name__ == "__main__":
    main()
