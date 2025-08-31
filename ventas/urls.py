# ventas/urls.py

from django.urls import path
from .views import (
    DashboardView,
    ProspectoListView, 
    ProspectoDetailView,
    ProspectoCreateView,
    ProspectoUpdateView,
    ProspectoDeleteView,
    add_interaccion,
    add_recordatorio,
    toggle_recordatorio,
    export_prospectos_excel,
    TrabajadorListView,
    TrabajadorCreateView,
    TrabajadorUpdateView,
    TrabajadorDeleteView,
    InteraccionUpdateView,
    InteraccionDeleteView,
    RecordatorioUpdateView,
    RecordatorioDeleteView,
    add_trabajador_a_prospecto,
    ProspectoTrabajadorUpdateView,
    ProspectoTrabajadorDeleteView,
    add_archivo,
    delete_archivo,
    CalendarioView,
    calendario_eventos,
)

urlpatterns = [
    # --- Dashboard ---
    path('', DashboardView.as_view(), name='dashboard'),

    # --- Prospectos ---
    path('prospectos/', ProspectoListView.as_view(), name='prospecto-list'),
    path('prospectos/export/', export_prospectos_excel, name='export-prospectos-excel'),
    path('prospecto/nuevo/', ProspectoCreateView.as_view(), name='prospecto-create'),
    path('prospecto/<int:pk>/', ProspectoDetailView.as_view(), name='prospecto-detail'),
    path('prospecto/<int:pk>/editar/', ProspectoUpdateView.as_view(), name='prospecto-update'),
    path('prospecto/<int:pk>/eliminar/', ProspectoDeleteView.as_view(), name='prospecto-delete'),
    
    # --- Acciones relacionadas a Prospectos ---
    path('prospecto/<int:prospecto_pk>/add-trabajador/', add_trabajador_a_prospecto, name='add-trabajador-a-prospecto'),
    path('prospecto/<int:prospecto_pk>/add-interaccion/', add_interaccion, name='add-interaccion'),
    path('prospecto/<int:prospecto_pk>/add-recordatorio/', add_recordatorio, name='add-recordatorio'),
    path('prospecto/<int:prospecto_pk>/add-archivo/', add_archivo, name='add-archivo'),
    
    # --- Interacciones ---
    path('interaccion/<int:pk>/editar/', InteraccionUpdateView.as_view(), name='interaccion-update'),
    path('interaccion/<int:pk>/eliminar/', InteraccionDeleteView.as_view(), name='interaccion-delete'),
    
    # --- Recordatorios ---
    path('recordatorio/<int:pk>/editar/', RecordatorioUpdateView.as_view(), name='recordatorio-update'),
    path('recordatorio/<int:pk>/eliminar/', RecordatorioDeleteView.as_view(), name='recordatorio-delete'),
    path('recordatorio/<int:pk>/toggle/', toggle_recordatorio, name='toggle-recordatorio'),
    
    # --- Trabajadores ---
    path('trabajadores/', TrabajadorListView.as_view(), name='trabajador-list'),
    path('trabajador/nuevo/', TrabajadorCreateView.as_view(), name='trabajador-create'),
    path('trabajador/<int:pk>/editar/', TrabajadorUpdateView.as_view(), name='trabajador-update'),
    path('trabajador/<int:pk>/eliminar/', TrabajadorDeleteView.as_view(), name='trabajador-delete'),

    # --- Relación Prospecto-Trabajador ---
    path('prospecto-trabajador/<int:pk>/editar/', ProspectoTrabajadorUpdateView.as_view(), name='prospecto-trabajador-update'),
    path('prospecto-trabajador/<int:pk>/eliminar/', ProspectoTrabajadorDeleteView.as_view(), name='prospecto-trabajador-delete'),
    
    # --- Archivos ---
    path('archivo/<int:pk>/eliminar/', delete_archivo, name='delete-archivo'),
    
    path('calendario/', CalendarioView.as_view(), name='calendario'),
    path('api/calendario-eventos/', calendario_eventos, name='calendario-eventos'),
]
    

