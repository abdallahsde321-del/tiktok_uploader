import os
import subprocess
import yt_dlp
from datetime import datetime, timedelta

# ================= الإعدادات =================
LINKS_FILE = "links.txt"
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

def get_videos_from_list():
    """قراءة الروابط أو المعرفات من ملف links.txt وتخطي ما تم رفعه مسبقاً"""
    if not os.path.exists(LINKS_FILE):
        print("[FATAL] ملف links.txt غير موجود!")
        return []
    
    with open(LINKS_FILE, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
    
    videos = []
    history = get_downloaded_history()
    
    for line in lines:
        vid_id = line.split("v=")[-1].split("/")[-1]
        if vid_id not in history:
            videos.append(vid_id)
            if len(videos) >= 180:
                break
    return videos

def download_video(video_id):
    print(f"[DOWNLOAD] جاري تحميل الفيديو: {video_id}...")
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'outtmpl': VIDEO_FILENAME,
        'format': 'best[ext=mp4]/best',
        'js_runtimes': {'deno': {}, 'node': {}},
        'quiet': False
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
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
        print(f"[SCHEDULE] سيتم جدولة الفيديو ليُنشر في: {formatted_time}")
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
    video_ids = get_videos_from_list()
    
    if not video_ids:
        print("لا توجد فيديوهات جديدة في ملف links.txt للرفع.")
        return
        
    print(f"تم العثور على {len(video_ids)} فيديو في القائمة. البدء في معالجتها وجدولتها...")
    now = datetime.now()
    
    for index, v_id in enumerate(video_ids):
        print(f"\n--- معالجة الفيديو ({index + 1}/{len(video_ids)}): {v_id} ---")
        
        is_downloaded = download_video(v_id)
        
        if is_downloaded:
            title = f"Shorts #{index + 1}"
            
            # توزيع الـ 180 فيديو على مدار الشهر (6 فيديوهات يومياً - فاصل 4 ساعات)
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
