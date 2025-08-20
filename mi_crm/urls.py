from django.contrib import admin
from django.urls import path, include
from ventas import views as ventas_views

urlpatterns = [
    path('admin/', admin.site.urls),
    # Rutas de autenticación de Django (login, logout, etc.)
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Rutas de la aplicación de ventas
    path('', ventas_views.DashboardView.as_view(), name='dashboard'),
    path('prospectos/', ventas_views.ProspectoListView.as_view(), name='prospecto-list'),
    path('prospecto/nuevo/', ventas_views.ProspectoCreateView.as_view(), name='prospecto-create'),
    path('prospecto/<int:pk>/', ventas_views.ProspectoDetailView.as_view(), name='prospecto-detail'),
    path('prospecto/<int:pk>/editar/', ventas_views.ProspectoUpdateView.as_view(), name='prospecto-update'),
    path('prospecto/<int:pk>/eliminar/', ventas_views.ProspectoDeleteView.as_view(), name='prospecto-delete'),
    
    # Rutas para añadir interacciones y recordatorios
    path('prospecto/<int:prospecto_pk>/add_interaccion/', ventas_views.add_interaccion, name='add-interaccion'),
    path('prospecto/<int:prospecto_pk>/add_recordatorio/', ventas_views.add_recordatorio, name='add-recordatorio'),
    path('recordatorio/<int:pk>/toggle/', ventas_views.toggle_recordatorio, name='toggle-recordatorio'),
    path('', include('ventas.urls')),
]