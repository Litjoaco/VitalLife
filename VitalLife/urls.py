from django.urls import path, include
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

# Importamos las vistas desde la app 'usuario'
from usuario import views as usuario_views
from paneladmin import views as paneladmin_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', usuario_views.inicio, name='inicio'),
    
    # Incluimos las URLs de la app 'usuario' bajo el prefijo 'cuenta/'
    path('cuenta/', include('usuario.urls')),

    path('logout/', auth_views.LogoutView.as_view(next_page='inicio'), name='logout'),
    path('panel-admin/', include('paneladmin.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)