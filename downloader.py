import yt_dlp
import os
import tempfile

class YouTubeDownloader:
    def __init__(self, output_dir="output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        self.ffmpeg_path = r"C:\ffmpeg-8.0.1-essentials_build\bin\ffmpeg.exe"
        
    def download_audio(self, url):
        """Завантаження зі створенням копії з простим іменем"""
        

        ydl_opts = {
            'format': 'worst[ext=mp4]+worstaudio[ext=m4a]/mp4',
            'outtmpl': os.path.join(self.output_dir, 'temp_%(id)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
        }
        
        try:
            print(f"🔗 Починаємо завантаження: {url}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Завантаження
                print("⬇️ Завантаження відео...")
                info = ydl.extract_info(url, download=True)
                temp_path = ydl.prepare_filename(info)
                
                # Створенно копії з простим ім'ям
                simple_name = f"audio_{info['id']}.mp4"
                simple_path = os.path.join(self.output_dir, simple_name)
                
                # Копіюємо файл з тимчасової папки до кінцевої з простим ім'ям
                import shutil
                shutil.copy2(temp_path, simple_path)
                
                # Перевіряємо розмір файлу
                if os.path.exists(simple_path):
                    file_size = os.path.getsize(simple_path)
                    print(f"✅ Відео завантажено: {simple_path}")
                    print(f"📊 Розмір: {file_size} байт")
                    
                    if file_size < 1024:
                        raise Exception(f"Файл занадто маленький: {file_size} байт")
                    
                    # Видаляємо тимчасовий файл
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                    
                    return simple_path
                else:
                    raise Exception("Файл не створено")
                    
        except Exception as e:
            print(f"❌ Помилка в download_audio: {e}")
            raise Exception(f"Помилка при завантаженні: {e}")

    def transcribe(self, audio_path):
        """Перетворення аудіо в текст"""
        
        try:
            print(f"🎤 Починаємо транскрипцію файла: {audio_path}")
            
            # Перевіряємо існування файлу
            if not os.path.exists(audio_path):
                raise Exception(f"Файл не знайдено: {audio_path}")
                
            # Перевіряємо розмір файлу
            file_size = os.path.getsize(audio_path)
            print(f"📊 Розмір файла: {file_size} байт")
            
            if file_size < 1024:  # Меньше 1KB
                raise Exception(f"Файл занадто маленький: {file_size} байт")
                
            # Перевіряємо доступ до файлу
            try:
                with open(audio_path, 'rb') as f:
                    f.read(1024)  # Читаємо перші 1024 байта
                print("✅ Файл доступний для чітання")
            except Exception as e:
                raise Exception(f"Немає доступу до файлу: {e}")
            
            # Перевіряємо формат файлу
            file_ext = os.path.splitext(audio_path)[1].lower()
            print(f"📁 Формат файлу: {file_ext}")
            
            # Транскрипція з автоматичним визначенням мови
            print("🔄 Виконуємо транскрипцію...")
            result = self.model.transcribe(
                audio_path,
                language=None,  # Автовизначення мови
                task='transcribe',
                verbose=True
            )
            
            # Вертаємо повний текст
            full_text = result["text"].strip()
            
            print(f"✅ Транскрипція завершена. Мова: {result['language']}")
            print(f"📝 Довжина тексту: {len(full_text)} символів")
            
            return full_text
            
        except Exception as e:
            print(f"❌ Помилка в transcribe: {e}")
            raise Exception(f"Помилка при транскрипції: {e}")