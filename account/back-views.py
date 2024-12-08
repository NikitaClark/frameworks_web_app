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
import json  
import hashlib  
import requests  
from datetime import timedelta  
from django.contrib.auth.decorators import login_required  
from django.shortcuts import render, redirect  
from django.http import JsonResponse
from django.utils import timezone  
from django.contrib.auth.models import Group  
from .models import Profile  
import json  
import hashlib  
import requests  
from datetime import timedelta  
from django.contrib.auth.decorators import login_required  
from django.shortcuts import render, redirect  
from django.http import JsonResponse
from django.utils import timezone  
from django.contrib.auth.models import Group  
from .models import Profile  
from django.views.decorators.csrf import csrf_exempt 
from django.http import HttpResponseBadRequest  
from video_app.views import create_thumbnail
from .models import InvoiceToken


logger = logging.getLogger(__name__)

@login_required
def activacions(request):
    if request.user.is_authenticated:  # Проверяем, авторизован ли пользователь
        profile = request.user.profile  # Получаем профиль пользователя
    else:
        profile = None  # Либо обрабатываем случай, если пользователь не авторизован

    return render(request, 'activacionsnew.html', {'profile': profile})
 

# Функция для создания платежа
@login_required
def create_payment(request):
    if request.method == 'POST':
        api_url = 'https://dashboard.reffer.ai/external/getInvoice'
        api_client = 'test_wizzeframeworks'
        api_token = 'test_emypbxQ1HViTttaM2dLG4Do2BIsdMbR3Js4mGdaD'      
        fp = hashlib.md5((request.META['REMOTE_ADDR'] + request.META['HTTP_USER_AGENT']).encode()).hexdigest()       
        amount = int(request.POST.get('amount'))
        if amount == 20:
            additional_tokens = 100
        elif amount == 10:
            additional_tokens = 50
        elif amount == 30:
            additional_tokens = 150
        else:
            additional_tokens = 0        
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
            'success_url': f'https://wizzeframeworks.com/account/success/?invoice={invoice}&amount={amount}',
            'auth': {'client': api_client, 'token': api_token},
            'additional_params': {'amount': str(amount), 'additional_tokens': str(additional_tokens), 'invoice': invoice}
        }
        try:
            response = requests.post(api_url, json=request_data)
            response.raise_for_status()     
            response_data = response.json()
            payment_url = response_data.get('url')    
            if payment_url:
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
    if request.user.is_authenticated: 
        profile = request.user.profile  
    else:
        profile = None  
    return render(request, 'activacionsnew.html', {'profile': profile})

@login_required
@csrf_exempt
def callback(request):
    invoice = request.GET.get('invoice')
    amount_param = request.GET.get('amount')

    if request.user.is_authenticated:
        print(f'Amount parameter received: {amount_param}, Invoice number: {invoice}')  
        
        if InvoiceToken.objects.filter(user=request.user, invoice_number=invoice).exists():
            return JsonResponse({'message': f'Tokens have already been credited for invoice: {invoice}'})
        
        try:
            profile, created = Profile.objects.get_or_create(user=request.user, defaults={'tokens': 0})
            
            if amount_param == '100':
                additional_tokens = 100
            elif amount_param == '150':
                additional_tokens = 150
            else:
                additional_tokens = 50

            profile.tokens += additional_tokens
            profile.group_activation_date = timezone.now()
            profile.group_expiration_date = profile.group_activation_date + timedelta(days=30)
            profile.invoice_number = invoice
            profile.save()

            invoice_token = InvoiceToken(user=request.user, invoice_number=invoice, tokens_credited=additional_tokens)
            invoice_token.save()

            return JsonResponse({'message': f'Callback successfully processed for invoice: {invoice}. User credited with {additional_tokens} tokens.'})

        except Exception as e:
            return JsonResponse({'error': 'Error processing the request'}, status=500)

    else:
        return JsonResponse({'error': 'User is not authenticated'}, status=401)


def success(request):
    invoice = request.GET.get('invoice')
    amount_param = request.GET.get('amount')
    profile = request.user.profile
    if request.user.is_authenticated:
        try:
            if InvoiceToken.objects.filter(user=request.user, invoice_number=invoice).exists():
                return render(request, 'activacionsnew.html', {'profile': profile, 'message': 'Tokens have already been credited for this invoice'})
            
            profile, created = Profile.objects.get_or_create(user=request.user, defaults={'tokens': 0})

            if amount_param == '20':
                additional_tokens = 100
            elif amount_param == '30':
                additional_tokens = 150
            else:
                additional_tokens = 50
            
            profile.tokens += additional_tokens
            profile.group_activation_date = timezone.now()
            profile.group_expiration_date = profile.group_activation_date + timedelta(days=30)
            profile.invoice_number = invoice
            profile.save()

            invoice_token = InvoiceToken(user=request.user, invoice_number=invoice, tokens_credited=additional_tokens)
            invoice_token.save()

            return render(request, 'success.html', {'invoice': invoice, 'additional_tokens': additional_tokens, 'profile': profile, 'amount_param': amount_param})

        except Exception as e:
            return render(request, 'activacionsnew.html', {'profile': profile, 'message': 'Error processing the request'})

    else:
        return render(request, 'activacionsnew.html', {'profile': profile, 'message': 'User is not authenticated'})
@login_required
def dashboard(request):
    # Проверка прав пользователя
    is_premium_member = request.user.groups.filter(name='premium').exists()
    is_basic_member = request.user.groups.filter(name='basic').exists()
    is_enterprises_member = request.user.groups.filter(name='enterprises').exists()
    
    # Инициализация переменной video_links
    video_links = VideoLink.objects.filter(user=request.user).order_by('-uploaded_at')
    
    # Пагинация
    paginator = Paginator(video_links, 8)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Получение профиля пользователя
    profile = Profile.objects.get(user=request.user)
    expiration_time = profile.group_expiration_date.timestamp() if profile.group_expiration_date else None
    current_time = timezone.now().timestamp()

    return render(request, 'main/dashboardnew.html', {
        'is_premium_member': is_premium_member,
        'is_basic_member': is_basic_member,
        'is_enterprises_member': is_enterprises_member,
        'video_links': video_links,  # Используйте инициализированную переменную
        'expiration_time': expiration_time,
        'current_time': current_time,
        'profile': profile,
        'page_obj': page_obj,
    })

def delete_video(request, video_id):
    video = VideoLink.objects.get(id=video_id)
    if video.user == request.user:
        video.delete()
        return redirect('dashboard') 
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
    if 'picture' in response:
        details['photo_url'] = response['picture']
    return details



def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        email = user_form.data.get('email')
        if User.objects.filter(email=email).exists():
            user_form.add_error('email', ValidationError("A user with this email address already exists."))
        recaptcha_response = request.POST.get('g-recaptcha-response')
        data = {
            'secret': settings.RECAPTCHA_SECRET_KEY,
            'response': recaptcha_response
        }
        response = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
        result = response.json()
        print("Response from reCAPTCHA:", json.dumps(result, indent=4))
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
    message = "A user with this email address already exists."
    return render(request, 'main/register.html', {'user_form': user_form, 'message': message})

@login_required
def edit(request):
    profile = request.user.profile 
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST)
        profile_form = ProfileEditForm(instance=profile, data=request.POST, files=request.FILES)
        if 'clear_photo' in request.POST:
            profile.photo = None  
            profile.save()  
            messages.success(request, 'Photo cleared successfully', extra_tags='edit')  # Добавляем тег 'edit' к сообщению
            return redirect('edit')  
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully', extra_tags='edit')  # Добавляем тег 'edit' к сообщению
            return redirect('edit')  
        else:
            messages.error(request, 'Error updating your profile', extra_tags='edit')  # Добавляем тег 'edit' к сообщению
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=profile)

    return render(request, 'main/editnew.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile  
    })
