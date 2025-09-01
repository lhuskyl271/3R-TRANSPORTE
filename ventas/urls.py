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
    ClienteCerradoListView,
    update_proyecto,
    add_entregable,
    add_seguimiento_proyecto,
    asignar_miembro_equipo,
    ProyectoDetailView,
    ProyectoFlujoTrabajoView,
    crear_columna_api,
    crear_tarea_api,
    mover_tarea_api,
    actualizar_columna_api,
    eliminar_columna_api,
    actualizar_tarea_api,
    eliminar_tarea_api,
    EntregableUpdateView, EntregableDeleteView,
    DesasignarMiembroEquipoView,
    SeguimientoProyectoUpdateView, SeguimientoProyectoDeleteView,guardar_diagrama_api,
    descargar_diagrama_pdf,DiagramaEditorView,reordenar_columnas_api,
    get_diagrama_api,
    guardar_diagrama_api,
    descargar_diagrama_pdf,
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

    # --- Clientes y Proyectos ---
    path('clientes/', ClienteCerradoListView.as_view(), name='cliente-cerrado-list'),
    # --- ✅ NUEVA RUTA PARA LA VISTA DE DETALLE DEL PROYECTO ---
    path('proyecto/<int:pk>/', ProyectoDetailView.as_view(), name='proyecto-detail'),

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

    # --- URLs PARA GESTIÓN DE PROYECTOS ---
    path('proyecto/<int:pk>/update/', update_proyecto, name='update-proyecto'),
    path('proyecto/<int:proyecto_pk>/add-entregable/', add_entregable, name='add-entregable'),
    path('proyecto/<int:proyecto_pk>/add-seguimiento/', add_seguimiento_proyecto, name='add-seguimiento-proyecto'),
    path('proyecto/<int:proyecto_pk>/asignar-miembro/', asignar_miembro_equipo, name='asignar-miembro-equipo'),
    
    # --- ✅ NUEVAS RUTAS PARA EL FLUJO DE TRABAJO (KANBAN) ---
    path('proyecto/<int:pk>/flujo-trabajo/', ProyectoFlujoTrabajoView.as_view(), name='proyecto-flujo-trabajo'),
    path('api/proyecto/<int:proyecto_pk>/columna/crear/', crear_columna_api, name='api-crear-columna'),
    path('api/columna/<int:columna_pk>/tarea/crear/', crear_tarea_api, name='api-crear-tarea'),
    path('api/tarea/mover/', mover_tarea_api, name='api-mover-tarea'),
    
    # --- 👇 LÍNEAS CORREGIDAS ---
    path('api/columna/<int:columna_pk>/actualizar/', actualizar_columna_api, name='api-actualizar-columna'),
    path('api/columna/<int:columna_pk>/eliminar/', eliminar_columna_api, name='api-eliminar-columna'),
    path('api/tarea/<int:tarea_pk>/actualizar/', actualizar_tarea_api, name='api-actualizar-tarea'),
    path('api/tarea/<int:tarea_pk>/eliminar/', eliminar_tarea_api, name='api-eliminar-tarea'),
    
     # --- URLs para CRUD de Entregables ---
    path('entregable/<int:pk>/editar/', EntregableUpdateView.as_view(), name='entregable-update'),
    path('entregable/<int:pk>/eliminar/', EntregableDeleteView.as_view(), name='entregable-delete'),
    
    # --- URL para eliminar miembro de equipo ---
    path('equipoproyecto/<int:pk>/eliminar/', DesasignarMiembroEquipoView.as_view(), name='desasignar-miembro'),

    # --- URLs para CRUD de Seguimiento ---
    path('seguimiento/<int:pk>/editar/', SeguimientoProyectoUpdateView.as_view(), name='seguimiento-update'),
    path('seguimiento/<int:pk>/eliminar/', SeguimientoProyectoDeleteView.as_view(), name='seguimiento-delete'),
    
    # ✅ NUEVA RUTA: Para abrir el editor gráfico y crear un nuevo diagrama
    path('proyecto/<int:proyecto_pk>/diagrama/crear/', DiagramaEditorView.as_view(), name='diagrama-crear'),
    
    # ✅ NUEVA RUTA: Para abrir el editor gráfico y editar un diagrama existente
    path('diagrama/<int:pk>/editar/', DiagramaEditorView.as_view(), name='diagrama-editar'),
    
    # ✅ NUEVA RUTA API: Para obtener los datos JSON de un diagrama
    path('api/diagrama/<int:diagrama_pk>/', get_diagrama_api, name='api-get-diagrama'),

    # Se mantiene la misma URL para guardar, pero su lógica cambiará
    path('api/proyecto/<int:proyecto_pk>/guardar-diagrama/', guardar_diagrama_api, name='api-guardar-diagrama'),
    path('diagrama/<int:diagrama_pk>/descargar-pdf/', descargar_diagrama_pdf, name='descargar-diagrama-pdf'),
     path('api/proyecto/<int:proyecto_pk>/reordenar-columnas/', reordenar_columnas_api, name='api-reordenar-columnas'),
]