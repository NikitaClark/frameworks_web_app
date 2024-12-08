from django.urls import path,include
from . import views
from video_app.views import download_video
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from .views import  video_list




urlpatterns = [
    path('', views.index, name='home'),
    path('contact', views.contact, name='contact'),
    path('upload', views.upload_form, name='upload_form'),
    path('', views.upload_form),
    path('upload/', views.upload_video, name='upload_video'),
    path('download/<str:dubbing_id>/<str:filename>/', views.download_video, name='download_video'),
    path('account/', include('account.urls')),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('account/', video_list, name='video_list'),

    path('upload_video/', views.upload_video, name='upload_video'),  

   
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns() 
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)