import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

try:
    from downloader import YouTubeDownloader
    from transcriber import SpeechTranscriber
    from summarizer import TextSummarizer
except ModuleNotFoundError as e:
    missing = getattr(e, "name", "unknown")
    help_text = (
        f"Не вистачає Python-модуля: {missing}\n\n"
        f"Python: {sys.executable}\n\n"
        "Встановіть залежності командою:\n"
        f"\"{sys.executable}\" -m pip install -r requirements.txt"
    )
    print(help_text)
    try:
        temp_root = tk.Tk()
        temp_root.withdraw()
        messagebox.showerror("Відсутні залежності", help_text)
        temp_root.destroy()
    except Exception:
        pass
    raise SystemExit(1)

class YouTubeSummarizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Video Summarizer")
        self.root.geometry("800x600")
        
        self.downloader = YouTubeDownloader()
        self.transcriber = SpeechTranscriber()
        self.summarizer = TextSummarizer()
        
        self.setup_ui()
        
    def setup_ui(self):
        title_label = tk.Label(self.root, text="Аналізатор YouTube відео", 
                              font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        link_frame = tk.Frame(self.root)
        link_frame.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(link_frame, text="Посилання на YouTube відео:").pack(anchor=tk.W)
        
        input_frame = tk.Frame(link_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        self.link_entry = tk.Entry(input_frame, font=("Arial", 12))
        self.link_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        paste_btn = tk.Button(input_frame, text="📋 Вставити", 
                             command=self.paste_from_clipboard, bg="lightyellow")
        paste_btn.pack(side=tk.RIGHT)
        

        self.link_entry.bind('<Control-v>', lambda e: self.paste_from_clipboard())
        self.link_entry.bind('<Control-V>', lambda e: self.paste_from_clipboard())
        
        self.create_context_menu()
        
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        self.analyze_btn = tk.Button(button_frame, text="Аналізувати відео", 
                                   command=self.start_analysis, bg="lightblue",
                                   font=("Arial", 12, "bold"))
        self.analyze_btn.pack(side=tk.LEFT, padx=5)
        
        self.browse_btn = tk.Button(button_frame, text="Вибрати файл", 
                                  command=self.browse_file, bg="lightgray")
        self.browse_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = tk.Button(button_frame, text="Зберегти конспект", 
                                command=self.save_summary, bg="lightgreen",
                                state=tk.DISABLED)
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.pack(pady=10, padx=20, fill=tk.X)
        
        result_frame = tk.Frame(self.root)
        result_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        tk.Label(result_frame, text="Результат:").pack(anchor=tk.W)
        
        self.notebook = ttk.Notebook(result_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        self.full_text_frame = tk.Frame(self.notebook)
        self.notebook.add(self.full_text_frame, text="Повний текст")
        
        self.full_text = scrolledtext.ScrolledText(self.full_text_frame, 
                                                  wrap=tk.WORD, font=("Arial", 10))
        self.full_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.summary_frame = tk.Frame(self.notebook)
        self.notebook.add(self.summary_frame, text="Конспект")
        
        self.summary_text = scrolledtext.ScrolledText(self.summary_frame, 
                                                     wrap=tk.WORD, font=("Arial", 10))
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.status_label = tk.Label(self.root, text="Готовий до роботи", 
                                   font=("Arial", 10), fg="green")
        self.status_label.pack(pady=5)
        
    def browse_file(self):
        """Вибір локального файлу"""
        filename = filedialog.askopenfilename(
            title="Оберіть аудіо файл",
            filetypes=[("Audio files", "*.mp3 *.wav *.m4a *.mp4")]
        )
        if filename:
            self.link_entry.delete(0, tk.END)
            self.link_entry.insert(0, filename)
            
    def paste_from_clipboard(self):
        """Вставка з буфера обміну"""
        try:
            clipboard_content = self.root.clipboard_get()
            self.link_entry.delete(0, tk.END)
            self.link_entry.insert(0, clipboard_content)
        except tk.TclError:
            messagebox.showwarning("Увага", "Буфер обміну порожній")
            
    def create_context_menu(self):
        """Створення контекстного меню для поля введення"""
        context_menu = tk.Menu(self.link_entry, tearoff=0)
        context_menu.add_command(label="Вставити", command=self.paste_from_clipboard, accelerator="Ctrl+V")
        context_menu.add_separator()
        context_menu.add_command(label="Копіювати", command=lambda: self.link_entry.event_generate("<<Copy>>"))
        context_menu.add_command(label="Вирізати", command=lambda: self.link_entry.event_generate("<<Cut>>"))
        context_menu.add_command(label="Очистити", command=lambda: self.link_entry.delete(0, tk.END))
        
        def show_context_menu(event):
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()
        
        self.link_entry.bind("<Button-3>", show_context_menu)
            
    def start_analysis(self):
        """Запуск процесу аналізу"""
        url_or_path = self.link_entry.get().strip()
        if not url_or_path:
            messagebox.showerror("Помилка", "Введіть посилання на відео або оберіть файл")
            return
            
        self.analyze_btn.config(state=tk.DISABLED)
        self.progress.start()
        self.status_label.config(text="Обробка...", fg="blue")
        
        thread = threading.Thread(target=self.process_video, args=(url_or_path,))
        thread.daemon = True
        thread.start()
        
    def process_video(self, source):
        """Обробка відео в окремому потоці"""
        try:
            if "youtube.com" in source or "youtu.be" in source:
                self.update_status("Завантаження аудіо з YouTube...")
                print(f"🔗 Завантаження з URL: {source}")
                audio_path = self.downloader.download_audio(source)
                print(f"✅ Файл завантажено: {audio_path}")
            else:
                audio_path = source
                print(f"📁 Використовуємо локальний файл: {audio_path}")
                
            if not os.path.exists(audio_path):
                raise Exception(f"Файл не знайдено: {audio_path}")
                
            file_size = os.path.getsize(audio_path)
            print(f"📊 Розмір файлу: {file_size} байт")
            
            if file_size < 1024:
                raise Exception(f"Файл занадто малий: {file_size} байт")
                
            self.update_status("Розпізнавання мови...")
            print("🎤 Починаємо транскрипцію...")
            full_text = self.transcriber.transcribe(audio_path)
            print(f"📝 Текст отримано, довжина: {len(full_text)} символів")
            
            self.update_status("Створення конспекту...")
            print("📋 Створюємо конспект...")
            summary = self.summarizer.create_summary(full_text)
            print("✅ Конспект готовий!")
            
            self.root.after(0, self.update_results, full_text, summary)
            
        except Exception as e:
            print(f"❌ Помилка в process_video: {e}")
            self.root.after(0, self.show_error, str(e))
            
    def update_results(self, full_text, summary):
        """Оновлення інтерфейсу з результатами"""
        self.full_text.delete(1.0, tk.END)
        self.full_text.insert(1.0, full_text)
        
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.insert(1.0, summary)
        
        self.progress.stop()
        self.analyze_btn.config(state=tk.NORMAL)
        self.save_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Готово!", fg="green")
        
    def update_status(self, message):
        """Оновлення рядка статусу"""
        self.root.after(0, lambda: self.status_label.config(text=message))
        
    def show_error(self, error_message):
        """Показ повідомлення про помилку"""
        self.progress.stop()
        self.analyze_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Помилка", fg="red")
        messagebox.showerror("Помилка", f"Виникла помилка: {error_message}")
        
    def save_summary(self):
        """Збереження конспекту у файл"""
        summary_content = self.summary_text.get(1.0, tk.END)
        if not summary_content.strip():
            messagebox.showwarning("Увага", "Немає конспекту для збереження")
            return
            
        filename = filedialog.asksaveasfilename(
            title="Зберегти конспект",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(summary_content)
                messagebox.showinfo("Успіх", "Конспект збережено!")
            except Exception as e:
                messagebox.showerror("Помилка", f"Не вдалося зберегти: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeSummarizerGUI(root)
    root.mainloop()