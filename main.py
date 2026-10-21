import os
import subprocess
import yt_dlp
from datetime import datetime, timedelta

# ================= الإعدادات =================
SOURCE_CHANNEL = "https://www.tiktok.com/@haitham.talaat01"
HISTORY_FILE = "history.txt"
VIDEO_FILENAME = "video_to_upload.mp4"
# =============================================

def get_downloaded_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().splitlines()

def save_to_history(video_id):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(video_id + "\n")

def fetch_channel_videos():
    print(f"[FETCH] جاري سحب روابط الفيديوهات من القناة...")
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
    }
    
    video_urls = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(SOURCE_CHANNEL, download=False)
            if 'entries' in result:
                for entry in result['entries']:
                    url = entry.get('url') or f"https://www.tiktok.com/@haitham.talaat01/video/{entry.get('id')}"
                    video_urls.append(url)
    except Exception as e:
        print(f"[ERROR] خطأ في جلب الفيديوهات: {e}")
        
    history = get_downloaded_history()
    return [url for url in video_urls if url not in history]

def download_video(video_url):
    print(f"[DOWNLOAD] جاري تحميل الفيديو: {video_url}...")
    
    # استخدام خيارات توافقية لتجاوز حظر الـ CDN على السيرفرات السحابية
    ydl_opts = {
        'outtmpl': VIDEO_FILENAME,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'quiet': False,
        'no_check_certificates': True,
        'geo_bypass': True,
    }

    if os.path.exists("cookies.txt") and os.path.getsize("cookies.txt") > 0:
        ydl_opts['cookiefile'] = 'cookies.txt'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        
        if os.path.exists(VIDEO_FILENAME):
            return True
        return False
    except Exception as e:
        print(f"[ERROR] خطأ في التحميل: {e}")
        return False

def upload_to_tiktok(video_path, title, schedule_time=None):
    print(f"[UPLOAD] جاري الرفع إلى تيك توك...")
    command = [
        "tiktok-uploader",
        "-v", video_path,
        "-d", title,
        "-c", "cookies.txt"
    ]
    
    if schedule_time:
        formatted_time = schedule_time.strftime("%Y-%m-%d %H:%M")
        command.extend(["-s", formatted_time])
        print(f"[SCHEDULE] سيتم جدولة الفيديو في: {formatted_time}")
    else:
        print(f"[PUBLIC] نشر الفوري.")

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        print("[UPLOAD] تم الرفع بنجاح!")
        return True
    else:
        print(f"[ERROR] فشل الرفع: {result.stderr}")
        return False

def main():
    video_urls = fetch_channel_videos()
    if not video_urls:
        print("لا توجد فيديوهات جديدة.")
        return
        
    total_videos = len(video_urls)
    print(f"تم العثور على {total_videos} فيديو.")
    
    now = datetime.now()
    total_minutes_in_month = 30 * 24 * 60
    interval_minutes = total_minutes_in_month / total_videos if total_videos > 0 else 64

    for index, v_url in enumerate(video_urls):
        print(f"\n--- معالجة الفيديو ({index + 1}/{total_videos}) ---")
        
        is_downloaded = download_video(v_url)
        if is_downloaded:
            title = f"Shorts #{index + 1}"
            schedule_time = None if index == 0 else now + timedelta(minutes=interval_minutes * index)
                
            success = upload_to_tiktok(VIDEO_FILENAME, title, schedule_time)
            if success:
                save_to_history(v_url)
                os.remove(VIDEO_FILENAME)
            else:
                save_to_history(v_url)
                if os.path.exists(VIDEO_FILENAME):
                    os.remove(VIDEO_FILENAME)
        else:
            print(f"[SKIP] تخطي الفيديو.")
            save_to_history(v_url)

    print(f"\n=== انتهت العملية بنجاح! ===")

if __name__ == "__main__":
    main()
