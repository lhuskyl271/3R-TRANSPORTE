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
    add_archivo
)

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('prospectos/', ProspectoListView.as_view(), name='prospecto-list'),
    path('prospectos/export/', export_prospectos_excel, name='export-prospectos-excel'),
    path('prospecto/nuevo/', ProspectoCreateView.as_view(), name='prospecto-create'),
    path('prospecto/<int:pk>/', ProspectoDetailView.as_view(), name='prospecto-detail'),
    path('prospecto/<int:pk>/editar/', ProspectoUpdateView.as_view(), name='prospecto-update'),
    path('prospecto/<int:pk>/eliminar/', ProspectoDeleteView.as_view(), name='prospecto-delete'),
    
    # --- RUTAS CORREGIDAS CON GUION BAJO ('_') ---
    path('prospecto/<int:prospecto_pk>/add_trabajador/', add_trabajador_a_prospecto, name='add_trabajador_a_prospecto'),
    path('prospecto/<int:prospecto_pk>/add_interaccion/', add_interaccion, name='add_interaccion'),
    path('prospecto/<int:prospecto_pk>/add_recordatorio/', add_recordatorio, name='add_recordatorio'),
    path('prospecto/<int:prospecto_pk>/add_archivo/', add_archivo, name='add_archivo'),
    
    path('interaccion/<int:pk>/editar/', InteraccionUpdateView.as_view(), name='interaccion_update'),
    path('interaccion/<int:pk>/eliminar/', InteraccionDeleteView.as_view(), name='interaccion_delete'),
    
    path('recordatorio/<int:pk>/editar/', RecordatorioUpdateView.as_view(), name='recordatorio_update'),
    path('recordatorio/<int:pk>/eliminar/', RecordatorioDeleteView.as_view(), name='recordatorio_delete'),
    path('recordatorio/<int:pk>/toggle/', toggle_recordatorio, name='toggle_recordatorio'),
    
    path('trabajadores/', TrabajadorListView.as_view(), name='trabajador-list'),
    path('trabajador/nuevo/', TrabajadorCreateView.as_view(), name='trabajador-create'),
    path('trabajador/<int:pk>/editar/', TrabajadorUpdateView.as_view(), name='trabajador-update'),
    path('trabajador/<int:pk>/eliminar/', TrabajadorDeleteView.as_view(), name='trabajador-delete'),

    path('prospecto-trabajador/<int:pk>/editar/', ProspectoTrabajadorUpdateView.as_view(), name='prospecto_trabajador_update'),
    path('prospecto-trabajador/<int:pk>/eliminar/', ProspectoTrabajadorDeleteView.as_view(), name='prospecto_trabajador_delete'),
]