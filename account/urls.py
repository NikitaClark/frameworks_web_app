from django.contrib import admin
from django.urls import path, include
from .views import  activacions,create_payment,callback,success
from django.contrib.auth import views as auth_views
from . import views
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
    #path('login/', auth_views.LoginView.as_view(), name='login'),
    #path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    # path('', views.dashboard, name='dashboard'),

    # path('password-change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    #path('password-change/done', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),

    #path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    #path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    # path('password-reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    #path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    path('', include('django.contrib.auth.urls')),
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('edit/', views.edit, name='edit'),
    path('activacions/', create_payment, name='activacions'),
    
    #path('activate-basic/', activate_basic, name='activate_basic'),
    #path('activate-premium/', activate_premium, name='activate_premium'),
    #path('activate-enterprises/', activate_enterprises, name='activate_enterprises'),
    
    path('activate/<uidb64>/<token>/', views.activate, name='activate'),
    path('delete-video/<int:video_id>/', views.delete_video, name='delete_video'),






    path('pay/', create_payment, name='create_payment'),

    path('delete-video/<int:video_id>/', views.delete_video, name='delete_video'),

    path('create-payment/', create_payment, name='create_payment'),


    path('callback/', callback, name='callback'),
    path('success/', success, name='success'),


]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

