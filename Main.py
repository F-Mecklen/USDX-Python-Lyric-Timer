import os
import re
import time
import requests
import yt_dlp as youtube_dl
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from pydub import AudioSegment
import pygame


# Step 1: Lyrics input and saving
def save_lyrics():
    input_prompt = input('Copy the lyrics into lyrics.txt and press any key to continue')



# Step 2: Download YouTube video and audio
def download_youtube_video(video_url, download_path, title):
    try:
        print(f"Starting download for: {video_url}")
        ydl_opts_video = {
            'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]',
            'outtmpl': os.path.join(download_path, f'{title}.%(ext)s'),
            'noplaylist': True,
            'nocheckcertificate': True,
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
        }
        ydl_opts_audio = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(download_path, f'{title}.%(ext)s'),
            'noplaylist': True,
            'nocheckcertificate': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with youtube_dl.YoutubeDL(ydl_opts_video) as ydl:
            ydl.extract_info(video_url, download=True)
        with youtube_dl.YoutubeDL(ydl_opts_audio) as ydl:
            ydl.download([video_url])
        video_path = os.path.join(download_path, f"{title}.mp4")
        audio_path = os.path.join(download_path, f"{title}.mp3")
        print("Video, Audio downloaded successfully")
        return video_path, audio_path
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None


# Step 3: Image search and download
def google_search_images(query):
    search_url = f"https://www.google.com/search?q={query}&source=lnms&tbm=isch"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    image_elements = soup.find_all('img')
    image_urls = [img['src'] for img in image_elements if 'src' in img.attrs]
    for url in image_urls:
        if url.startswith('http'):
            return url
    return None


def download_image(url, save_path):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    img.save(save_path, 'PNG')


# Step 4: Split lyrics into syllables
def split_lyrics(lyrics_path):
    with open(lyrics_path, 'r') as f:
        lyrics = f.read()
    words = lyrics.split()
    syllables = [word for word in words]
    return syllables


# Step 5: Display lyrics and record timings
class TextRenderer:
    def __init__(self, syllables, temp_wav_path):
        pygame.init()
        self.screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption('Syllable Display')
        self.font = pygame.font.Font(None, 74)
        self.syllables = syllables
        self.current_syllable_idx = 0
        self.song_length = AudioSegment.from_wav(temp_wav_path).duration_seconds
        self.temp_wav_path = temp_wav_path

    def play_song(self):
        pygame.mixer.init()
        pygame.mixer.music.load(self.temp_wav_path)
        pygame.mixer.music.play()

    def update_display(self):
        self.screen.fill((0, 0, 0))
        if self.current_syllable_idx < len(self.syllables):
            current_syllable = self.syllables[self.current_syllable_idx]
            text = self.font.render(current_syllable, True, (255, 255, 255))
            self.screen.blit(text, (400 - text.get_width() // 2, 250 - text.get_height() // 2))
            next_syllable_idx = self.current_syllable_idx + 1
            for i in range(1, 5):
                if next_syllable_idx < len(self.syllables):
                    next_text = self.font.render(self.syllables[next_syllable_idx], True, (200, 200, 200))
                    self.screen.blit(next_text,
                                     (400 - next_text.get_width() // 2, 250 - text.get_height() // 2 + i * 50))
                    next_syllable_idx += 1
        pygame.display.flip()

    def run(self):
        running = True
        timestamps = []
        self.play_song()
        self.update_display()
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_f:
                        if self.current_syllable_idx < len(self.syllables):
                            current_time_ms = pygame.mixer.music.get_pos()
                            start_time = current_time_ms / 1000.0
                            if len(timestamps) > 0:
                                last_start_time = timestamps[-1][1]
                                syllable_duration = start_time - last_start_time
                            else:
                                syllable_duration = 0
                            timestamps.append(
                                (self.syllables[self.current_syllable_idx], start_time, syllable_duration))
                            print(
                                f"Start time {start_time:.2f} seconds for the syllable '{self.syllables[self.current_syllable_idx]}'")
                            self.current_syllable_idx += 1
                            self.update_display()
                        else:
                            running = False
                    elif event.key == pygame.K_ESCAPE:
                        running = False
        pygame.quit()
        return timestamps


def save_output(syllable_data, output_path):
    with open(output_path, 'w') as f:
        for syllable, start_time, duration in syllable_data:
            f.write(f"Name: {syllable}, at second {start_time / 2 :.2f} for {duration:.2f} seconds\n")


# Step 6: Convert timestamps to Ultrastar format
def parse_input_file(input_filename):
    with open(input_filename, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    return lines


def generate_ultrastar_file(output_filename, lines, bpm, artist, song_title):
    with open(output_filename, 'w', encoding='utf-8') as file:
        file.write(f"#TITLE:{song_title}\n")
        file.write(f"#ARTIST:{artist}\n")
        file.write(f"#BPM:{bpm}\n")
        file.write(f"#GAP:0\n")
        file.write(f"#MP3:{song_title}_{artist}.mp3\n")
        file.write(f"#VIDEO:{song_title}_{artist}.mp4\n")
        file.write(f"#COVER:{song_title}_{artist}.png\n")
        for i in range(len(lines)):
            line = lines[i]
            match = re.match(r'Name: (.+), at second (\d+\.\d+) for (\d+\.\d+) seconds', line)
            if match:
                name = match.group(1)
                second = float(match.group(2))
                length = float(match.group(3))
                calculated_second = ((second * bpm * 4) / 60)
                calculated_length = ((length * bpm * 4) / 60)
                file.write(f"R {calculated_second:.0f} {calculated_length:.0f} 0 {name}\n")
        file.write("E\n")


# Step 7: Adjust numbers in Ultrastar file
def adjust_numbers(input_file, output_file):
    with open(input_file, 'r') as infile:
        lines = infile.readlines()
    adjusted_lines = []
    for i in range(len(lines)):
        line = lines[i]
        if line.startswith('R'):
            parts = line.split()
            if len(parts) < 3:
                adjusted_lines.append(line + ' ')
                continue
            try:
                first_number = int(parts[1])
                second_number = int(parts[2])
            except ValueError:
                adjusted_lines.append(line)
                continue
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                next_parts = next_line.split()
                if len(next_parts) >= 2 and (next_parts[0] == 'R' or next_parts[0].endswith('-')):
                    try:
                        next_number = int(next_parts[1])
                    except ValueError:
                        adjusted_lines.append(line)
                        continue
                    current_sum = first_number + second_number
                    if current_sum > next_number:
                        second_number = next_number - first_number
                        parts[2] = str(second_number)
                        line = ' '.join(parts) + ' ' + '\n'
        adjusted_lines.append(line)
    with open(output_file, 'w') as outfile:
        outfile.writelines(adjusted_lines)


# Step 8: Process files for final output
def process_files(lyrics_file, words_file, output_file):
    with open(lyrics_file, 'r') as f:
        lyrics_lines = f.readlines()
    last_words = [line.split()[-1].strip() for line in lyrics_lines if line.split()]
    with open(words_file, 'r') as f:
        words_lines = f.readlines()
    words_info = []
    for line in words_lines:
        parts = line.split()
        if len(parts) > 4 and parts[0] == 'R':
            word = parts[4].strip()
            number = parts[1].strip()
            words_info.append((word, number, line.strip()))
        else:
            words_info.append((None, None, line.strip()))
    output_lines = []
    last_idx = 0
    total_lines = len(words_info)
    for i in range(total_lines):
        word, number, line = words_info[i]
        output_lines.append(line)
        if word and last_idx < len(last_words) and word == last_words[last_idx]:
            if i + 1 < total_lines and words_info[i + 1][0] is not None:
                next_number = words_info[i + 1][1]
                output_lines.append(f"- {next_number}")
            last_idx += 1
    with open(output_file, 'w') as out:
        for line in output_lines:
            out.write(line + ' \n')


def main():
    # Step 1: Save lyrics
    save_lyrics()

    # Step 2: Download YouTube video and audio
    video_url = input("Video Link:")
    song_title = input("Enter the song title: ")
    artist = input("Enter the artist: ")
    download_base_path = input("Enter save location:")
    download_path = os.path.join(download_base_path, f"{song_title}_{artist}")
    if not os.path.exists(download_path):
        os.makedirs(download_path)
    full_title = f"{song_title}_{artist}"
    video_path, audio_path = download_youtube_video(video_url, download_path, full_title)
    if video_path and audio_path:
        print(f"Video saved at: {video_path}")
        print(f"Audio saved at: {audio_path}")
    else:
        print("Download failed.")

    # Step 3: Image search and download
    query = f"{song_title} {artist} coverart"
    print(f"Searching for images for: {query}")
    image_url = google_search_images(query)
    if not image_url:
        print("No image found")
    else:
        save_path = os.path.join(download_path, f"{full_title}.png")
        download_image(image_url, save_path)
        print(f"Image saved at: {save_path}")

    # Step 4: Split lyrics into syllables
    lyrics_path = 'lyrics.txt'
    syllables = split_lyrics(lyrics_path)

    # Step 5: Play WAV and render lyrics
    temp_wav_path = 'temp_song.wav'
    song = AudioSegment.from_mp3(audio_path)
    song = song._spawn(song.raw_data, overrides={"frame_rate": int(song.frame_rate * 0.5)})
    song.set_frame_rate(44100)
    song.export(temp_wav_path, format="wav")
    renderer = TextRenderer(syllables, temp_wav_path)
    timestamps = renderer.run()
    save_output(timestamps, 'output_se.txt')
    os.remove(temp_wav_path)

    # Step 6: Generate Ultrastar file
    bpm = float(input("Bpm: "))
    input_lines = parse_input_file('output_se.txt')
    generate_ultrastar_file('ultrastar_output.txt', input_lines, bpm, artist, song_title)

    # Step 7: Adjust numbers in Ultrastar file
    adjust_numbers('ultrastar_output.txt', 'adjusted_output.txt')

    # Step 8: Process files for final output
    process_files('lyrics.txt', 'adjusted_output.txt', 'fin_output.txt')


if __name__ == "__main__":
    main()
