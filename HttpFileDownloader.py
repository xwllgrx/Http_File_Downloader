import http.client
import os
import sys
import threading
import time
from urllib.parse import urlparse, urljoin

def download_file(url):                                                 # функция для загрузки файла по переданному URL
    parsed_url = urlparse(url)                                          # разбирает URL по частям (схема, домен, путь и т.д.)
    if not parsed_url.scheme or not parsed_url.netloc:
        print("Invalid URL")
        return

    connection = http.client.HTTPConnection(parsed_url.netloc)          # установка HTTP-соединения
    connection.request("GET", parsed_url.path or "/")
    response = connection.getresponse()

    if response.status != 200:
        print(f"HTTP Error: {response.status} {response.reason}")
        return

    filename = os.path.basename(parsed_url.path) or "downloaded_file"   # имя файла из URL и размер
    total_size = int(response.getheader('Content-Length', 0))
    if total_size > 0:
        print(f"Content-Length from server: {total_size} bytes")

    progress = {"downloaded": 0, "lock": threading.Lock()}              # процесс загрузки (поток для отображения прогресса)

    def progress_reporter():
        while not stop_event.is_set():
            with progress["lock"]:
                downloaded = progress["downloaded"]
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"Downloaded: {downloaded} bytes ({percent:.2f}%)")
                else:
                    print(f"Downloaded: {downloaded} bytes")
            time.sleep(1)

    stop_event = threading.Event()
    reporter_thread = threading.Thread(target=progress_reporter)
    reporter_thread.start()

    try:                                                                # загрузка файла (Открывает файл для записи)
        with open(filename, "wb") as f: 
            while chunk := response.read(1024):
                with progress["lock"]:
                    progress["downloaded"] += len(chunk)
                f.write(chunk)

        actual_size = os.path.getsize(filename)                         # проверка размера файла
        print(f"Actual file size: {actual_size} bytes")
        if total_size > 0 and actual_size != total_size:
            print(f"Warning: Actual size ({actual_size} bytes) does not match Content-Length ({total_size} bytes).")

    except Exception as e:                                              # обработка ошибок
        print(f"Error during download: {e}")

    finally:
        stop_event.set()
        reporter_thread.join()
        connection.close()

    print(f"Download completed. File saved as '{filename}'.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <URL>")
        sys.exit(1)

    url = sys.argv[1]
    try:
        download_file(url)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
