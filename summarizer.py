import re
import os
from collections import Counter
import math

class TextSummarizer:
    def __init__(self):
        # Стоп-слова для української та англійської мов
        self.ukrainian_stopwords = {
            'і', 'в', 'на', 'з', 'до', 'за', 'по', 'від', 'при', 'про', 'для', 
            'це', 'той', 'та', 'але', 'як', 'що', 'не', 'ні', 'то', 'все', 'ще', 'вже',
            'я', 'ти', 'він', 'вона', 'воно', 'ми', 'ви', 'вони', 'мені', 'тобі', 'йому',
            'їй', 'нас', 'вас', 'їх', 'мене', 'тебе', 'його', 'її', 'нас', 'вас', 'їх'
        }
        
        self.english_stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 
            'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        }
        
    def create_summary(self, text, max_sentences=5):
        """Створення конспекту з тексту"""
        
        if not text or len(text.strip()) < 50:
            return "Текст занадто короткий для створення конспекту."
            
        try:
            # Крок 1: Застосовуємо користувацькі виправлення (наприклад, звід -> звіт)
            text = self.apply_user_corrections(text)
            
            # Крок 2: Розділяємо текст на речення
            sentences = self.split_into_sentences(text)
            
            # Якщо речень дуже мало (менше 3), повертаємо текст як є
            if len(sentences) < 3:
                return text + "\n\n[ℹ️ Примітка: Текст занадто короткий для формування конспекту]"
                
            # Крок 3: Очищаємо та токенізуємо текст для аналізу частот слів
            words = self.preprocess_text(text)
            
            # Крок 4: Обчислюємо важливість кожного речення
            sentence_scores = self.calculate_sentence_scores(sentences, words)
            
            # Крок 5: Вибираємо найважливіші речення
            # Обмежуємо кількість: або max_sentences, або кількість наявних речень
            actual_max = min(max_sentences, len(sentences))
            top_sentences = self.select_top_sentences(sentences, sentence_scores, actual_max)
            
            # Крок 6: Формуємо фінальний конспект
            summary = self.format_summary(top_sentences, text)
            
            return summary
            
        except Exception as e:
            return f"Помилка при створенні конспекту: {e}"
            
    def apply_user_corrections(self, text):
        """Застосування користувацьких виправлень до тексту"""
        
        # Словник виправлень для української мови
        corrections = {
            'звід': 'звіт',
            'мати муть особий': 'матимуть особи',
            'мати муть особа': 'матимуть особа',
            'подивати': 'подавати',
        }
        
        import re
        fixed_text = text
        
        print(f"🔧 Застосовуємо виправлення до тексту довжиною {len(text)} символів")
        
        corrections_applied = 0
        for wrong, correct in corrections.items():
            # Шукаємо слово цілком (враховуємо межі слова \b)
            pattern = r'\b' + re.escape(wrong) + r'\b'
            matches = re.findall(pattern, fixed_text, flags=re.IGNORECASE)
            
            if matches:
                print(f"🔍 Знайдено '{wrong}' {len(matches)} раз(а)")
                
            # Замінюємо всі входження (з урахуванням регістру)
            new_text = re.sub(pattern, correct, fixed_text, flags=re.IGNORECASE)
            
            if new_text != fixed_text:
                corrections_applied += 1
                print(f"✅ Виправлено: '{wrong}' -> '{correct}'")
                fixed_text = new_text
        
        if corrections_applied == 0:
            print("⚠️ Жодного виправлення не застосовано")
        else:
            print(f"✅ Застосовано {corrections_applied} виправлень")
        
        return fixed_text
            
    def split_into_sentences(self, text):
        """Розділення тексту на речення (враховує переноси рядків Whisper)"""
        # Whisper часто пише кожне речення з нового рядка (\n)
        # Тому спочатку розбиваємо на рядки, потім по пунктуації
        lines = text.split('\n')
        sentences = []

        for line in lines:
            # Розбиваємо рядок по крапках, знаках оклику та питання
            parts = re.split(r'[.!?]+', line)
            for part in parts:
                cleaned = part.strip()
                # Ігноруємо дуже короткі шматки (сміття)
                if len(cleaned) > 10:
                    sentences.append(cleaned)

        return sentences
        
    def preprocess_text(self, text):
        """Попередня обробка тексту: очищення та видалення стоп-слів"""
        # Приводимо до нижнього регістру та видаляємо пунктуацію
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Токенізація (розбиття на слова)
        words = text.split()
        
        # Видаляємо стоп-слова та занадто короткі слова
        filtered_words = [
            word for word in words 
            if len(word) > 2 and 
            word not in self.ukrainian_stopwords and 
            word not in self.english_stopwords
        ]
        
        return filtered_words
        
    def calculate_sentence_scores(self, sentences, words):
        """Обчислення важливості речень на основі частоти слів"""
        # Підраховуємо частоту кожного слова
        word_freq = Counter(words)
        
        # Нормалізація частот (ділимо на максимальну частоту)
        max_freq = max(word_freq.values()) if word_freq else 1
        
        sentence_scores = {}
        
        for sentence in sentences:
            # Токенізація конкретного речення
            sentence_words = self.preprocess_text(sentence)
            
            if not sentence_words:
                continue
                
            # Підрахунок важливості речення (сума нормалізованих частот слів)
            score = sum(word_freq.get(word, 0) / max_freq for word in sentence_words)
            
            # Нормалізація за довжиною речення (щоб довгі речення не мали переваги)
            if len(sentence_words) > 0:
                score = score / math.sqrt(len(sentence_words))
                
            sentence_scores[sentence] = score
            
        return sentence_scores
        
    def select_top_sentences(self, sentences, scores, max_sentences):
        """Вибір найкращих речень та відновлення їх оригінального порядку"""
        # Сортуємо речення за важливістю (від більшого до меншого)
        sorted_sentences = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Вибираємо топ речення, запам'ятовуючи їх індекси
        top_sentences = []
        used_indices = set()
        
        for sentence, score in sorted_sentences[:max_sentences]:
            # Знаходимо індекс речення в оригінальному списку
            for i, s in enumerate(sentences):
                if s == sentence and i not in used_indices:
                    top_sentences.append((i, sentence))
                    used_indices.add(i)
                    break
                    
        # Сортуємо обрані речення за оригінальним порядком появи в тексті
        top_sentences.sort(key=lambda x: x[0])
        
        # Повертаємо список речень без індексів
        return [sentence for _, sentence in top_sentences]
        
    def format_summary(self, sentences, original_text):
        """Форматування конспекту з заголовком та статистикою"""
        if not sentences:
            return "Не вдалося створити конспект."
            
        # Визначаємо мову за наявністю українських символів
        has_ukrainian = bool(re.search(r'[іїєґ]', original_text.lower()))
        
        header = "📝 КОНСПЕКТ\n" + "="*50 + "\n\n"
        
        if has_ukrainian:
            header += f"📊 Кількість речень у конспекті: {len(sentences)}\n"
            header += f"📝 Оригінальний текст: {len(original_text)} символів\n\n"
        else:
            header += f"📊 Sentences in summary: {len(sentences)}\n"
            header += f"📝 Original text: {len(original_text)} characters\n\n"
        
        # Збираємо речення разом
        content = "\n\n".join(sentences)
        
        return header + content