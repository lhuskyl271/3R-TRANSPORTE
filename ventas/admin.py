from django.contrib import admin
from .models import Etiqueta, Prospecto, Interaccion, Recordatorio

@admin.register(Etiqueta)
class EtiquetaAdmin(admin.ModelAdmin):
    search_fields = ('nombre',)

@admin.register(Prospecto)
class ProspectoAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'email', 'estado', 'asignado_a', 'fecha_creacion')
    list_filter = ('estado', 'asignado_a', 'fecha_creacion', 'etiquetas')
    search_fields = ('nombre_completo', 'email', 'empresa')
    filter_horizontal = ('etiquetas',)
    date_hierarchy = 'fecha_creacion'
    raw_id_fields = ('asignado_a',)

@admin.register(Interaccion)
class InteraccionAdmin(admin.ModelAdmin):
    list_display = ('prospecto', 'tipo', 'fecha', 'creado_por')
    list_filter = ('tipo', 'fecha')
    search_fields = ('prospecto__nombre_completo', 'notas')
    date_hierarchy = 'fecha'
    raw_id_fields = ('prospecto', 'creado_por')

@admin.register(Recordatorio)
class RecordatorioAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'prospecto', 'fecha_recordatorio', 'completado', 'creado_por')
    list_filter = ('completado', 'fecha_recordatorio')
    search_fields = ('titulo', 'prospecto__nombre_completo')
    raw_id_fields = ('prospecto', 'creado_por')