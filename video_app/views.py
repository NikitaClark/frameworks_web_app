import logging
import os
import time
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import FileResponse
from elevenlabs.client import ElevenLabs
from django.conf import settings
import subprocess
from account.models import VideoLink
from datetime import datetime
from django.shortcuts import render
from account.models import Profile
from django.shortcuts import get_object_or_404
import logging
from django.contrib.auth.models import User
from moviepy.editor import VideoFileClip
import random
from django.contrib.auth.tokens import default_token_generator
from concurrent.futures import ThreadPoolExecutor
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
import uuid  

# Set API key for ElevenLabs
ELEVENLABS_API_KEY = 'c598d59242da3e15bb2d9bd776529ee0'

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def index(request):
    return render(request, 'main/index.html')

def contact(request):
    return render(request, 'main/contact.html')

def upload_form(request):
    profile = Profile.objects.get(user=request.user)
    return render(request, 'main/upload.html', {
    'profile': profile 
})

def convert_to_mp4(input_file_path, output_file_path, quality='medium', resolution='original'):
    """
    Конвертирует видео в формат MP4 с использованием FFmpeg с возможностью выбора разрешения и качества.
    """
    # Присваиваем битрейт в зависимости от уровня качества
    if quality == 'high':
        video_bitrate = '5000k'
        audio_bitrate = '320k'
    elif quality == 'medium':
        video_bitrate = '2500k'
        audio_bitrate = '128k'
    else:  # low
        video_bitrate = '1000k'
        audio_bitrate = '64k'

    # Присваиваем параметры для разрешения
    resolution_map = {
        '240p': '426x240',
        '360p': '640x360',
        '720p': '1280x720',
        '1080p': '1920x1080',
        'original': None  # Исходное разрешение
    }
    scale_option = resolution_map.get(resolution, None)

    # Проверяем, чтобы выходной файл не совпадал с исходным
    if input_file_path == output_file_path:
        base, ext = os.path.splitext(output_file_path)
        output_file_path = f"{base}_converted.mp4"
    
    ffmpeg_path = r'/home/ubuntu/frameworks/bin/ffmpeg'  # Укажите полный путь до ffmpeg.exe
    command = [
        ffmpeg_path, '-i', input_file_path,
        '-c:v', 'libx264', '-b:v', video_bitrate,
        '-c:a', 'aac', '-b:a', audio_bitrate,
        '-strict', 'experimental'
    ]

    # Добавляем опцию изменения разрешения, если выбрано не "original"
    if scale_option:
        command.extend(['-vf', f'scale={scale_option}'])

    command.append(output_file_path)
    
    try:
        subprocess.run(command, check=True)
        logging.debug(f"Видео конвертировано в MP4 с разрешением {resolution} и качеством {quality}: {output_file_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Ошибка при конвертации видео: {e}")
        raise

    return output_file_path

def get_video_duration(file_path):
    """
    Получает длительность видео в секундах с помощью FFmpeg./usr/bin/ffmpeg
    """
    logging.error(f"123")  
    command = ['C:\\ffmpeg\\bin\\ffmpeg', '-i', file_path]
    logging.error(f"67")  
    result = subprocess.run(command, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    logging.error(f"456")  
    # Обработка результата для извлечения длительности
    output = result.stderr.decode()
    duration_line = next((line for line in output.splitlines() if "Duration" in line), None)

    if duration_line:
        duration_str = duration_line.split(",")[0].split("Duration: ")[1]
        hours, minutes, seconds = map(float, duration_str.split(":"))
        return hours * 3600 + minutes * 60 + seconds

    raise Exception("Не удалось получить длительность видео")
def create_thumbnail(video_path, dubbing_id, filename):
    try:
        clip = VideoFileClip(video_path)
        duration = clip.duration

        random_time = random.uniform(0, duration)
        thumbnail_path = os.path.join(settings.MEDIA_ROOT, 'dubbing', dubbing_id, filename)
        os.makedirs(os.path.dirname(thumbnail_path), exist_ok=True)  # Создаем директорию, если она не существует
        
        clip.save_frame(thumbnail_path, t=random_time)
        
        # Возвращаем относительный путь
        return os.path.join('media', 'dubbing', dubbing_id, filename)
    except Exception as e:
        logging.error(f"Error creating thumbnail for {video_path}: {e}")
        return None
MAX_THREADS = 5  

def handle_video_processing(file_path, target_language, quality, resolution, profile):  
    try:  
        logging.debug(file_path)  
        # Проверка длительности видео  
        duration = get_video_duration(file_path)  
        tokens_needed = int(duration // 60) + (1 if duration % 60 > 0 else 0)  

        # Проверяем, достаточно ли токенов у пользователя  
        if profile.tokens < tokens_needed:  
            raise ValueError('There are not enough tokens to process this video')  

        # Списание токенов  
        profile.tokens -= tokens_needed  
        profile.save()  
        # Конвертация видео  
        mp4_output_path = os.path.splitext(file_path)[0] + '.mp4'  
        convert_to_mp4(file_path, mp4_output_path, quality=quality, resolution=resolution)  

        client = ElevenLabs(api_key=ELEVENLABS_API_KEY)  
        output_video_path, dubbing_id = process_video_with_elevenlabs(client, mp4_output_path, target_language)  

        # Создание миниатюры после обработки видео  
        thumbnail_path = create_thumbnail(output_video_path, dubbing_id, f"{os.path.basename(output_video_path)}.png")  

        # Возвращаем необходимые данные для сохранения  
        return output_video_path, thumbnail_path, dubbing_id  

    except Exception as e:  
        print(e)
        logging.error(f"Ошибка при обработке видео: {e}")  
        return None, None, None  

def send_download_link_email(user_email, download_link):
    subject = 'Your video is ready to upload'
    message = f'Your video is successfully processed. You can download it from the following link: https://wizzeframeworks.com{download_link}'
    from_email = settings.DEFAULT_FROM_EMAIL  # Убедитесь, что у вас настроен EMAIL_BACKEND и DEFAULT_FROM_EMAIL в settings.py
    
    try:
        send_mail(subject, message, from_email, [user_email])
        logging.info(f'Email sent to {user_email} with download link.')
    except Exception as e:
        logging.error(f'Error sending email to {user_email}: {e}')

# Изменяем функцию upload_video
def upload_video(request):  
    logging.debug("Upload video requested")  
    profile = Profile.objects.get(user=request.user)  
    if request.method == 'POST':  
        if 'file' not in request.FILES:  
            return JsonResponse({'success': False, 'message': 'No file uploaded'})  

        file = request.FILES['file']  
        target_language = request.POST.get('language')  
        quality = request.POST.get('quality', 'medium')  
        resolution = request.POST.get('resolution', 'original')  

        if file.name == '':  
            return JsonResponse({'success': False, 'message': 'No file selected'})  

        if not target_language:  
            return JsonResponse({'success': False, 'message': 'No target language selected'})  

        # Создание уникального имени файла  
        file_name, file_extension = os.path.splitext(file.name)  
        unique_file_name = f"{file_name}_{uuid.uuid4()}{file_extension}"  
        file_path = os.path.join(settings.MEDIA_ROOT, unique_file_name)  

        with open(file_path, 'wb+') as destination:  
            for chunk in file.chunks():  
                destination.write(chunk)  

        try:  
            with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:  
                logging.debug("Submitting video processing to thread pool")  
                future = executor.submit(handle_video_processing, file_path, target_language, quality, resolution, profile)  
                output_video_path, thumbnail_path, dubbing_id = future.result()  

            logging.debug(f"Video processing completed: {output_video_path}, {thumbnail_path}, {dubbing_id}")  

            if output_video_path is None:  
                os.remove(file_path)  
                return JsonResponse({'success': False, 'message': 'Ошибка при обработке видео. Попробуйте позже.'})  

            output_video_filename = os.path.basename(output_video_path)  
            download_link = f'/download/{dubbing_id}/{output_video_filename}'  
            send_download_link_email(request.user.email, download_link)  
            os.remove(file_path)  
            
            video_link = VideoLink(  
                user=request.user,  
                link=download_link,  
                filename=output_video_filename,  
                file_path=output_video_path,  
                thumbnail_path=thumbnail_path  
            )  
            video_link.save()  

            return JsonResponse({'success': True, 'download_link': download_link})  

        except Exception as e:  
            logging.error(f"Error during video processing: {e}")  
            os.remove(file_path)  # Удаляем файл, если произошла ошибка  
            return JsonResponse({'success': False, 'message': 'Ошибка при обработке видео. Попробуйте позже.'})  

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})  

def video_list(request):
    video_links = VideoLink.objects.filter(user=request.user).order_by('-uploaded_at')[:5]
    logging.debug(f"Retrieved video links: {video_links}")

    for video in video_links:
        # Используем file_path для доступа к видео
        thumbnail_path = create_thumbnail(video.file_path.path, video.dubbing_id, f"{video.filename}.png")
        
        # Предположим, что у вас есть поле для хранения пути к миниатюре
        video.thumbnail_path = thumbnail_path  # или аналогичное поле
        video.save()  # Не забудьте сохранить изменения

    return render(request, 'main/account.html', {'video_links': video_links})



def download_video(request, dubbing_id, filename):
    # Формируем правильный путь к файлу
    file_path = os.path.join(settings.MEDIA_ROOT, 'dubbing', dubbing_id, filename)

    # Проверка существования файла
    if not os.path.exists(file_path):
        logging.error(f"File not found: {file_path}")
        messages.error(request, 'Запрашиваемый файл не существует.')
        return redirect('upload_form')

    logging.debug(f"File found: {file_path}")  # Логируем найденный файл
    try:
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)
    except Exception as e:
        logging.error(f"Ошибка при открытии файла: {e}")
        messages.error(request, 'Ошибка при загрузке файла.')
        return redirect('upload_form')

def download_dubbed_file(client, dubbing_id: str, language_code: str) -> str:
    """
    Downloads the dubbed file for the specified dubbing ID and language code.
    Saves the file directly to the dubbing folder.
    """
    
    dir_path = f"{dubbing_id}"
    # Define the file path directly in the dubbing folder.
    file_path = os.path.join(settings.MEDIA_ROOT, 'dubbing', f"{dir_path}/{language_code}.mp4")
    
    # Make sure the dubbing directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    try:
        # Write the dubbed file to the specified path.
        with open(file_path, "wb") as file:
            for chunk in client.dubbing.get_dubbed_file(dubbing_id, language_code):
                file.write(chunk)
        logging.debug(f"Dubbed file saved to: {file_path}")
    except Exception as e:
        logging.error(f"Error writing dubbed file: {e}")
        raise

    return file_path

def wait_for_dubbing_completion(client, dubbing_id: str) -> bool:
    """
    Waits for the dubbing process to complete by checking the status periodically.
    """
    MAX_ATTEMPTS = 120
    CHECK_INTERVAL = 10  # In seconds

    for _ in range(MAX_ATTEMPTS):
        metadata = client.dubbing.get_dubbing_project_metadata(dubbing_id)
        if metadata.status == "dubbed":
            return True
        elif metadata.status == "dubbing":
            logging.debug("Dubbing in progress... Will check status again in {} seconds.".format(CHECK_INTERVAL))
            time.sleep(CHECK_INTERVAL)
        else:
            logging.error("Dubbing failed: {}".format(metadata.error_message))
            return False
            logging.error("Dubbing timed out")
    return False

def process_video_with_elevenlabs(client, video_path, target_language):
    with open(video_path, 'rb') as video_file:
        dubbing_response = client.dubbing.dub_a_video_or_an_audio_file(
            file=video_file,
            target_lang=target_language,
        )

    logging.debug(f"Full Response: {dubbing_response}")

    # Получаем dubbing_id
    dubbing_id = dubbing_response.dubbing_id
    if not dubbing_id:
        raise Exception("Dubbing ID not found in the response.")

    # Ожидаем завершения дубляжа
    if wait_for_dubbing_completion(client, dubbing_id):
        output_video_path = download_dubbed_file(client, dubbing_id, target_language)
        return output_video_path, dubbing_id  # Возвращаем также dubbing_id
    else:
        raise Exception("Dubbed video failed or did not complete successfully.")
    
    
    