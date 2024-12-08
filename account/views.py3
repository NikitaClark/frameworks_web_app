from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login
from .forms import UserRegistrationForm, UserEditForm, ProfileEditForm
from django.contrib.auth.decorators import login_required
from .models import Profile
from django.contrib import messages
from django.contrib.auth.models import Group
from django.http import JsonResponse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.contrib import messages
from account.models import VideoLink
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import logging
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import requests
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.conf import settings
import threading
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import Group
import time
from django.utils import timezone
import json
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404



@login_required
def activacions(request):
    if request.user.is_authenticated:  # Проверяем, авторизован ли пользователь
        profile = request.user.profile  # Получаем профиль пользователя
    else:
        profile = None  # Либо обрабатываем случай, если пользователь не авторизован

    return render(request, 'activacionsnew.html', {'profile': profile})

@login_required
def story(request):
    video_links = VideoLink.objects.filter(user=request.user).order_by('-uploaded_at')
    paginator = Paginator(video_links, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'main/story.html', {
        'page_obj': page_obj
    })
    
def remove_group_and_reset_tokens_after_delay(user, group_name, delay):
    def run():
        time.sleep(delay)  # Задержка в секундах
        
        # Удаляем группу
        group = Group.objects.filter(name=group_name).first()
        if group:
            user.groups.remove(group)

        # Обнуляем количество токенов
        profile = Profile.objects.get(user=user)
        profile.tokens = 0  # Обнуляем токены
        profile.save()

    thread = threading.Thread(target=run)
    thread.start()

def remove_all_groups(user):
    user.groups.clear()  # Удаляем все группы у пользователя

import json  
import hashlib  
import requests  
from datetime import timedelta  
from django.contrib.auth.decorators import login_required  
from django.shortcuts import render, redirect  
from django.http import JsonResponse, HttpResponseRedirect  
from django.utils import timezone  
from django.contrib.auth.models import Group  
from .models import Profile  

import json  
import hashlib  
import requests  
from datetime import timedelta  
from django.contrib.auth.decorators import login_required  
from django.shortcuts import render, redirect  
from django.http import JsonResponse, HttpResponseRedirect  
from django.utils import timezone  
from django.contrib.auth.models import Group  
from .models import Profile  
from django.views.decorators.csrf import csrf_protect

logger = logging.getLogger(__name__)

 #Функция для создания платежа
def create_payment(request):
    if request.method == 'POST':
        api_url = 'https://dashboard.reffer.ai/external/getInvoice'
        api_client = 'test_wizzeframeworks'
        api_token = 'test_emypbxQ1HViTttaM2dLG4Do2BIsdMbR3Js4mGdaD'
        
        fp = hashlib.md5((request.META['REMOTE_ADDR'] + request.META['HTTP_USER_AGENT']).encode()).hexdigest()
        amount = 10
        currency = 'USD'
        invoice = timezone.now().strftime('%Y%m%d%H%M%S')
        
        request_data = {
            'product': 'basic_subscription',
            'amount': amount,
            'currency': currency,
            'subscription': 'None',
            'invoice': invoice,
            'fp': fp,
            'callback_url': f'https://wizzeframeworks.com/account/callback/',
            'success_url': f'https://wizzeframeworks.com/account/success/?invoice={invoice}',
            'auth': {'client': api_client, 'token': api_token}
        }

        try:
            response = requests.post(api_url, json=request_data)
            response.raise_for_status()
            
            response_data = response.json()
            payment_url = response_data.get('url')
            
            if payment_url:
                logger.info(f'Получен URL для оплаты: {payment_url}')
                
                # Отправка запроса к callback для начисления токенов
                callback_response = requests.get(f'https://wizzeframeworks.com/account/callback/?invoice={invoice}')
                callback_response.raise_for_status()

                return redirect(payment_url)
            else:
                error_message = response_data.get('error_message')
                if error_message:
                    messages.error(request, f'Произошла ошибка при получении URL для оплаты: {error_message}')
                else:
                    messages.error(request, f'Не удалось получить URL для оплаты. Ответ от API: {response_data}')
        except requests.exceptions.RequestException as e:
            messages.error(request, f'Произошла ошибка при обращении к API: {e}')
        except ValueError:
            messages.error(request, 'Ответ от сервера не является корректным JSON.')
    
    else:
        messages.warning(request, 'Метод запроса не поддерживается.')

    return render(request, 'payments/pay.html')

@csrf_exempt
@login_required
def callback(request):
    from .models import Profile
    
    invoice = request.GET.get('invoice')

    logger.info('Callback функция была вызвана.')
    logger.info(f'Получен инвойс: {invoice}')
    
    if request.user.is_authenticated:
        try:
            profile, created = Profile.objects.get_or_create(user=request.user, defaults={'tokens': 0})
            profile.tokens += 100
            profile.group_activation_date = timezone.now()
            profile.group_expiration_date = profile.group_activation_date + timedelta(days=30)

            profile.save()

            logger.info(f'Начислено 100 токенов пользователю {request.user.username} за успешную оплату с инвойсом: {invoice}')

            return JsonResponse({'message': f'Callback успешно обработан для инвойса: {invoice}. Пользователю начислено 100 токенов.'})
        except Exception as e:
            logger.error(f'Ошибка при обработке callback: {str(e)}')
            return JsonResponse({'error': 'Ошибка при обработке запроса'}, status=500)
    else:
        return JsonResponse({'error': 'Пользователь не аутентифицирован'}, status=401)
    
def success(request):
    invoice = request.GET.get('invoice')
    callback_response = callback(request)
    return render(request, 'success.html', {'invoice': invoice})

@login_required
def activate_premium(request):
    if request.method == 'POST':
        remove_all_groups(request.user)
        premium_group, created = Group.objects.get_or_create(name='premium')
        request.user.groups.add(premium_group)

        profile = Profile.objects.get(user=request.user)
        profile.tokens += 100
        profile.group_activation_date = timezone.now()
        profile.group_expiration_date = profile.group_activation_date + timedelta(days=30)  # 1 месяц
        profile.save()

        request.user.save()
        return redirect('dashboard')

    return render(request, 'main/activate_premium.html')

@login_required
def activate_enterprises(request):
    if request.method == 'POST':
        remove_all_groups(request.user)
        enterprises_group, created = Group.objects.get_or_create(name='enterprises')
        request.user.groups.add(enterprises_group)

        profile = Profile.objects.get(user=request.user)
        profile.tokens += 150
        profile.group_activation_date = timezone.now()
        profile.group_expiration_date = profile.group_activation_date + timedelta(days=180)  # 6 месяцев
        profile.save()

        request.user.save()
        return redirect('dashboard')

    return render(request, 'main/activate_enterprises.html')

@login_required
def deactivate_premium(request):
    request.user.groups.clear()
    request.user.save()
    return redirect('dashboard')
@login_required
def dashboard(request):
    is_premium_member = request.user.groups.filter(name='premium').exists()
    is_basic_member = request.user.groups.filter(name='basic').exists()
    is_enterprises_member = request.user.groups.filter(name='enterprises').exists()

    video_links = VideoLink.objects.filter(user=request.user).order_by('-uploaded_at')
    paginator = Paginator(video_links, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    profile = Profile.objects.get(user=request.user)
    expiration_time = profile.group_expiration_date.timestamp() if profile.group_expiration_date else None
    current_time = timezone.now().timestamp()

    return render(request, 'main/dashboardnew.html', {
        'is_premium_member': is_premium_member,
        'is_basic_member': is_basic_member,
        'is_enterprises_member': is_enterprises_member,
        'video_links': video_links,
        'expiration_time': expiration_time,
        'current_time': current_time,
        'profile': profile,
        'page_obj': page_obj,
    })
def delete_video(request, video_id):
    video = VideoLink.objects.get(id=video_id)
    # Проверка на то, что пользователь имеет право удалять это видео
    if video.user == request.user:
        video.delete()
        return redirect('dashboard')  # Перенаправляем пользователя обратно на страницу dashboard после удаления
    else:
        return HttpResponse('У вас нет прав на удаление этого видео.')    
    
def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)

        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            messages.success(request, 'Your account has been activated! You can now log in')
            return redirect('login')  # Перенаправление на страницу входа
        else:
            messages.error(request, 'Activation link is invalid or expired')
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    return render(request, 'main/activation_invalid.html')


def get_user_details(strategy, details, response, *args, **kwargs):
    """
    Получаем информацию о пользователе из ответа.
    Убедитесь, что профиль пользователя включает photo_url.
    """
    if 'picture' in response:
        details['photo_url'] = response['picture']
    return details



def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)

        # Проверка на существующий email
        email = user_form.data.get('email')
        if User.objects.filter(email=email).exists():
            user_form.add_error('email', ValidationError("A user with this email address already exists."))

        # Проверка reCAPTCHA
        recaptcha_response = request.POST.get('g-recaptcha-response')
        data = {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = response.json()

        print("Response from reCAPTCHA:", json.dumps(result, indent=4))

        # Проверка успешности reCAPTCHA
        if not result.get('success'):
            error_codes = result.get('error-codes', [])
            error_message = "Please complete the reCAPTCHA."
            if error_codes:
                error_message += " Errors: " + ', '.join(error_codes)
            user_form.add_error(None, ValidationError(error_message))
        
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data['password'])
            new_user.is_active = False
            new_user.save()

            profile = Profile.objects.create(user=new_user)
            profile.tokens = 1
            
            # Получаем URL фото
            photo_url = request.POST.get('photo_url')
            if 'provider' in request.POST:
                provider = request.POST['provider']
                if photo_url:  
                    try:
                        response = requests.get(photo_url)
                        if response.status_code == 200:
                            file_name = f"user_photos/{new_user.username}.jpg"
                            profile.photo.save(file_name, ContentFile(response.content), save=True)
                    except Exception as e:
                        print("Error retrieving the image:", e)

            profile.save()
            
            # Генерация токена и отправка письма
            token = default_token_generator.make_token(new_user)
            uid = urlsafe_base64_encode(force_bytes(new_user.pk))
            activation_link = reverse('activate', kwargs={'uidb64': uid, 'token': token})
            activation_url = f"{request.scheme}://{request.get_host()}{activation_link}"

            email_subject = "Подтверждение вашей учетной записи"
            email_message = render_to_string('main/activation_email.html', {
                'user': new_user,
                'activation_url': activation_url,
            })
            send_mail(email_subject, email_message, 'pr.mgok@mail.ru', [new_user.email])

            return render(request, 'main/register_done.html', {'new_user': new_user})
    
    else:
        user_form = UserRegistrationForm()
    
    # Передача сообщения об ошибке в контекст для отображения на странице
    message = "A user with this email address already exists."
    return render(request, 'main/register.html', {'user_form': user_form, 'message': message})

@login_required
def edit(request):
    # Получаем профиль пользователя
    profile = request.user.profile  # или Profile.objects.get(user=request.user)

    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST)
        profile_form = ProfileEditForm(instance=profile, data=request.POST, files=request.FILES)

        # Обработка нажатия кнопки "Очистить фото"
        if 'clear_photo' in request.POST:
            profile.photo = None  # Очищаем фото
            profile.save()  # Сохраняем изменения профиля
            messages.success(request, 'Photo cleared successfully')
            return redirect('edit')  # Перенаправляем обратно на страницу редактирования

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully')
            return redirect('edit')  # Или куда-то еще по вашему желанию
        else:
            messages.error(request, 'Error updating your profile')

    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=profile)

    return render(request, 'main/editnew.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile  # Добавляем профиль в контекст
    })
