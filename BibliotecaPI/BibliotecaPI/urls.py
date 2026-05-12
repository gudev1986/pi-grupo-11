from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from diagnostico import diagnostico_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('usuarios/', include('apps.usuarios.urls')),
    path('catalogo/', include('apps.catalogo.urls')),
    path('acervo/', include('apps.acervo.urls')),
    path('circulacao/', include('apps.circulacao.urls')),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('importacao/', include('apps.importacao.urls')),
    path('_diagnostico/', diagnostico_view),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
