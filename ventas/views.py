# ventas/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from .models import Prospecto, Interaccion, Recordatorio, Etiqueta, Trabajador, ProspectoTrabajador, ArchivoAdjunto
from .forms import (
    ProspectoForm, InteraccionForm, RecordatorioForm, TrabajadorForm, 
    ProspectoTrabajadorForm, ProspectoTrabajadorUpdateForm, ArchivoAdjuntoForm
)
from django.db.models import Count, Q, Avg, Max, Case, When, F, IntegerField
from django.http import HttpResponseForbidden, HttpResponse
from openpyxl import Workbook
from django.contrib import messages
from django.db.models.functions import ExtractDay, Now, Extract
from openpyxl.styles import Font, Alignment
from django.utils import timezone
import json
from datetime import timedelta
import pytz 
from django.core.paginator import Paginator


# ==============================================================================
# MIXINS Y VISTAS BASE
# ==============================================================================

class OwnerRequiredMixin:
    """
    Mixin para asegurar que solo el superusuario o el usuario asignado
    puedan modificar objetos relacionados a un prospecto.
    """
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        
        asignado = None
        if isinstance(obj, Prospecto):
            asignado = obj.asignado_a
        elif isinstance(obj, (Interaccion, Recordatorio, ProspectoTrabajador, ArchivoAdjunto)):
            asignado = obj.prospecto.asignado_a
        
        if asignado and asignado != self.request.user and not self.request.user.is_superuser:
            raise HttpResponseForbidden("No tienes permiso para realizar esta acción.")
        return obj

# ==============================================================================
# VISTAS DEL DASHBOARD Y PROSPECTOS
# ==============================================================================

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'ventas/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        try:
            user_timezone = pytz.timezone('America/Mexico_City') 
        except pytz.UnknownTimeZoneError:
            user_timezone = pytz.timezone(timezone.get_default_timezone_name())

        hoy = timezone.now().astimezone(user_timezone)
        
        prospectos_qs = Prospecto.objects.all()
        if not user.is_superuser:
            prospectos_qs = prospectos_qs.filter(asignado_a=user)

        context['total_prospectos'] = prospectos_qs.count()
        
        quince_dias_atras = hoy - timedelta(days=15)
        context['prospectos_nuevos'] = prospectos_qs.filter(
            estado=Prospecto.Estado.NUEVO,
            fecha_creacion__gte=quince_dias_atras
        ).count()
        
        context['clientes_ganados'] = prospectos_qs.filter(estado=Prospecto.Estado.GANADO).count()
        
        reporte_data = prospectos_qs.values('estado').annotate(total=Count('estado')).order_by('estado')
        estado_display_map = dict(Prospecto.Estado.choices) 
        chart_data = {
            "labels": [estado_display_map.get(item['estado'], item['estado']) for item in reporte_data],
            "data": [item['total'] for item in reporte_data],
        }
        context['chart_data_json'] = json.dumps(chart_data)
        
        promedio_calificaciones = ProspectoTrabajador.objects.filter(
            prospecto__in=prospectos_qs
        ).values('trabajador__nombre').annotate(promedio=Avg('calificacion')).order_by('-promedio')
        context['promedio_calificaciones_trabajador'] = promedio_calificaciones

        from django.db.models import Subquery, OuterRef
        ultima_interaccion_subquery = Interaccion.objects.filter(
            prospecto=OuterRef('pk')
        ).order_by('-fecha').values('fecha')[:1]
        
        prospectos_inactivos = prospectos_qs.exclude(
            estado__in=[Prospecto.Estado.GANADO, Prospecto.Estado.PERDIDO]
        ).annotate(
            ultima_interaccion=Subquery(ultima_interaccion_subquery)
        ).annotate(
            dias_inactivo=Case(
                When(
                    ultima_interaccion__isnull=True, 
                    then=ExtractDay(Now() - F('fecha_creacion'))
                ),
                When(
                    ultima_interaccion__isnull=False,
                    then=ExtractDay(Now() - F('ultima_interaccion'))
                ),
                output_field=IntegerField()
            )
        ).filter(
            dias_inactivo__gte=1
        ).order_by('-dias_inactivo')
        
        page_size = int(self.request.GET.get('page_size', 10))
        paginator = Paginator(prospectos_inactivos, page_size)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context['prospectos_inactivos'] = page_obj
        context['seguimiento_requerido_count'] = prospectos_inactivos.count()

        quince_dias_despues = hoy + timedelta(days=15)
        recordatorios_proximos = Recordatorio.objects.filter(
            prospecto__in=prospectos_qs, completado=False, 
            fecha_recordatorio__gte=hoy, fecha_recordatorio__lte=quince_dias_despues
        ).select_related('prospecto').order_by('fecha_recordatorio')
        context['recordatorios_proximos'] = recordatorios_proximos
        
        recordatorios_pasados = Recordatorio.objects.filter(
            prospecto__in=prospectos_qs, 
            completado=False, 
            fecha_recordatorio__lt=hoy
        ).select_related('prospecto').order_by('fecha_recordatorio')
        context['recordatorios_pasados'] = recordatorios_pasados
        
        return context


class ProspectoListView(LoginRequiredMixin, ListView):
    model = Prospecto
    template_name = 'ventas/prospecto_list.html'
    context_object_name = 'prospectos'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(asignado_a=self.request.user)

        estado_filter = self.request.GET.get('estado')
        if estado_filter:
            queryset = queryset.filter(estado=estado_filter)
        
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(nombre_completo__icontains=query) |
                Q(email__icontains=query) |
                Q(empresa__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        base_qs = self.model.objects.all()
        if not self.request.user.is_superuser:
            base_qs = base_qs.filter(asignado_a=self.request.user)

        status_counts_dict = {
            item['estado']: item['total'] 
            for item in base_qs.values('estado').annotate(total=Count('id'))
        }

        status_cards_data = []
        for value, name in Prospecto.Estado.choices:
            status_cards_data.append({
                'value': value,
                'name': name,
                'count': status_counts_dict.get(value, 0)
            })

        context['status_cards'] = status_cards_data
        context['total_prospectos_global'] = base_qs.count()
        return context

class ProspectoDetailView(LoginRequiredMixin, OwnerRequiredMixin, DetailView):
    model = Prospecto
    template_name = 'ventas/prospecto_detail.html'
    context_object_name = 'prospecto'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['interaccion_form'] = InteraccionForm()
        context['recordatorio_form'] = RecordatorioForm()
        context['trabajador_form'] = ProspectoTrabajadorForm()
        context['archivo_form'] = ArchivoAdjuntoForm() 
        context['archivos_adjuntos'] = self.object.archivos_adjuntos.all()
        
        trabajadores_asociados_ids = self.object.trabajadores.values_list('id', flat=True)
        context['trabajador_form'].fields['trabajador'].queryset = Trabajador.objects.exclude(id__in=trabajadores_asociados_ids)
        
        context['relaciones_trabajadores'] = self.object.prospectotrabajador_set.all().select_related('trabajador')
        context['interacciones'] = self.object.interacciones.all().order_by('-fecha')
        context['recordatorios'] = self.object.recordatorios.all().order_by('completado', 'fecha_recordatorio')
        return context
    
class ProspectoCreateView(LoginRequiredMixin, CreateView):
    model = Prospecto
    form_class = ProspectoForm
    template_name = 'ventas/prospecto_form.html'
    
    def form_valid(self, form):
        form.instance.asignado_a = self.request.user
        messages.success(self.request, f"Prospecto '{form.instance.nombre_completo}' creado exitosamente.")
        return super().form_valid(form)

class ProspectoUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = Prospecto
    form_class = ProspectoForm
    template_name = 'ventas/prospecto_form.html'
    
    def form_valid(self, form):
        messages.success(self.request, f"Prospecto '{self.object.nombre_completo}' actualizado correctamente.")
        return super().form_valid(form)

class ProspectoDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Prospecto
    template_name = 'ventas/prospecto_confirm_delete.html'
    success_url = reverse_lazy('prospecto-list')

    def form_valid(self, form):
        messages.success(self.request, f"Prospecto '{self.object.nombre_completo}' ha sido eliminado.")
        return super().form_valid(form)

class TrabajadorListView(LoginRequiredMixin, ListView):
    model = Trabajador
    template_name = 'ventas/trabajador_list.html'
    context_object_name = 'trabajadores'
    paginate_by = 15

class TrabajadorCreateView(LoginRequiredMixin, CreateView):
    model = Trabajador
    form_class = TrabajadorForm
    template_name = 'ventas/trabajador_form.html'
    success_url = reverse_lazy('trabajador-list')

class TrabajadorUpdateView(LoginRequiredMixin, UpdateView):
    model = Trabajador
    form_class = TrabajadorForm
    template_name = 'ventas/trabajador_form.html'
    success_url = reverse_lazy('trabajador-list')

class TrabajadorDeleteView(LoginRequiredMixin, DeleteView):
    model = Trabajador
    template_name = 'ventas/trabajador_confirm_delete.html'
    success_url = reverse_lazy('trabajador-list')

@login_required
def add_trabajador_a_prospecto(request, prospecto_pk):
    prospecto = get_object_or_404(Prospecto, pk=prospecto_pk)
    if request.method == 'POST':
        form = ProspectoTrabajadorForm(request.POST)
        if form.is_valid():
            trabajador = form.cleaned_data['trabajador']
            if ProspectoTrabajador.objects.filter(prospecto=prospecto, trabajador=trabajador).exists():
                messages.error(request, f"El empleado '{trabajador.nombre}' ya está asignado a este prospecto.")
            else:
                relacion = form.save(commit=False)
                relacion.prospecto = prospecto
                relacion.save()
                messages.success(request, f"¡El empleado '{relacion.trabajador.nombre}' fue asignado correctamente!")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error en el campo '{form.fields[field].label}': {error}")
    return redirect('prospecto-detail', pk=prospecto_pk)

class ProspectoTrabajadorUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = ProspectoTrabajador
    form_class = ProspectoTrabajadorUpdateForm
    template_name = 'ventas/prospecto_trabajador_form.html'

    def get_success_url(self):
        messages.success(self.request, f"Se actualizó la calificación para '{self.object.trabajador.nombre}'.")
        return reverse('prospecto-detail', kwargs={'pk': self.object.prospecto.pk})

class ProspectoTrabajadorDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = ProspectoTrabajador
    template_name = 'ventas/prospecto_trabajador_confirm_delete.html'
    
    def get_success_url(self):
        messages.success(self.request, f"Se eliminó la relación con '{self.object.trabajador.nombre}'.")
        return reverse('prospecto-detail', kwargs={'pk': self.object.prospecto.pk})

@login_required
def add_interaccion(request, prospecto_pk):
    prospecto = get_object_or_404(Prospecto, pk=prospecto_pk)
    if request.method == 'POST':
        form = InteraccionForm(request.POST)
        if form.is_valid():
            interaccion = form.save(commit=False)
            interaccion.prospecto = prospecto
            interaccion.creado_por = request.user
            interaccion.save()
            messages.success(request, "Interacción registrada.")
    return redirect('prospecto-detail', pk=prospecto_pk)

class InteraccionUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = Interaccion
    form_class = InteraccionForm
    template_name = 'ventas/interaccion_form.html'
    def get_success_url(self):
        messages.success(self.request, "Interacción actualizada.")
        return reverse('prospecto-detail', kwargs={'pk': self.object.prospecto.pk})

class InteraccionDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Interaccion
    template_name = 'ventas/interaccion_confirm_delete.html'
    def get_success_url(self):
        messages.success(self.request, "Interacción eliminada.")
        return reverse('prospecto-detail', kwargs={'pk': self.object.prospecto.pk})

@login_required
def add_recordatorio(request, prospecto_pk):
    prospecto = get_object_or_404(Prospecto, pk=prospecto_pk)
    if request.method == 'POST':
        form = RecordatorioForm(request.POST)
        if form.is_valid():
            recordatorio = form.save(commit=False)
            recordatorio.prospecto = prospecto
            recordatorio.creado_por = request.user
            recordatorio.save()
            messages.success(request, "Recordatorio creado.")
    return redirect('prospecto-detail', pk=prospecto_pk)

class RecordatorioUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = Recordatorio
    form_class = RecordatorioForm
    template_name = 'ventas/recordatorio_form.html'
    def get_success_url(self):
        messages.success(self.request, "Recordatorio actualizado.")
        return reverse('prospecto-detail', kwargs={'pk': self.object.prospecto.pk})

class RecordatorioDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Recordatorio
    template_name = 'ventas/recordatorio_confirm_delete.html'
    def get_success_url(self):
        messages.success(self.request, "Recordatorio eliminado.")
        return reverse('prospecto-detail', kwargs={'pk': self.object.prospecto.pk})

@login_required
def toggle_recordatorio(request, pk):
    recordatorio = get_object_or_404(Recordatorio, pk=pk)
    if recordatorio.prospecto.asignado_a != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("No tienes permiso.")
    
    recordatorio.completado = not recordatorio.completado
    recordatorio.save()
    status = "completado" if recordatorio.completado else "marcado como pendiente"
    messages.info(request, f"Recordatorio '{recordatorio.titulo}' {status}.")
    return redirect('prospecto-detail', pk=recordatorio.prospecto.pk)

@login_required
def export_prospectos_excel(request):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    timestamp = timezone.now().strftime('%Y-%m-%d_%H-%M')
    response['Content-Disposition'] = f'attachment; filename="prospectos_{timestamp}.xlsx"'
    
    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'Prospectos'
    
    headers = [
        'Nombre Completo', 'Email', 'Teléfono', 'Empresa', 'Puesto', 'Estado', 
        'Interés', 'Calificación Prom.', 'Referido Por', 'Contacto Ref.',
        'Detalle Interés', 'Trabajadores', 'Etiquetas', 'Asignado a', 'Fecha Creación'
    ]
    for col_num, header_title in enumerate(headers, 1):
        cell = worksheet.cell(row=1, column=col_num, value=header_title)
        cell.font = Font(bold=True)

    prospectos_qs = Prospecto.objects.annotate(
        promedio_calificacion=Avg('prospectotrabajador__calificacion')
    )
    if not request.user.is_superuser:
        prospectos_qs = prospectos_qs.filter(asignado_a=request.user)
    
    prospectos = prospectos_qs.select_related('asignado_a').prefetch_related('etiquetas', 'trabajadores')

    for row_num, prospecto in enumerate(prospectos, 2):
        calificacion_str = f"{prospecto.promedio_calificacion:.2f}" if prospecto.promedio_calificacion else "N/A"
        row_data = [
            prospecto.nombre_completo, prospecto.email, prospecto.telefono, prospecto.empresa, prospecto.puesto,
            prospecto.get_estado_display(), prospecto.get_interes_principal_display(), calificacion_str,
            prospecto.referencio, prospecto.contacto_referencio, prospecto.interes_cliente,
            ", ".join([t.nombre for t in prospecto.trabajadores.all()]),
            ", ".join([e.nombre for e in prospecto.etiquetas.all()]),
            prospecto.asignado_a.username if prospecto.asignado_a else '',
            prospecto.fecha_creacion.strftime('%Y-%m-%d %H:%M') if prospecto.fecha_creacion else ''
        ]
        for col_num, cell_value in enumerate(row_data, 1):
            worksheet.cell(row=row_num, column=col_num, value=cell_value)
    
    for i, column_cells in enumerate(worksheet.columns):
        try:
            max_length = 0
            column = chr(65 + i)
            for cell in column_cells:
                if cell.value:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
            adjusted_width = (max_length + 2)
            worksheet.column_dimensions[column].width = adjusted_width
        except:
            pass
            
    workbook.save(response)
    return response

# --- FUNCIÓN MODIFICADA PARA CAPTURAR ERRORES ---
@login_required
def add_archivo(request, prospecto_pk):
    """
    Gestiona la subida de un nuevo archivo adjunto para un prospecto específico.
    """
    # 1. Obtiene el objeto del prospecto al que se adjuntará el archivo.
    #    Si no se encuentra, devuelve un error 404.
    prospecto = get_object_or_404(Prospecto, pk=prospecto_pk)

    # 2. Procesa el formulario solo si la petición es de tipo POST.
    if request.method == 'POST':
        # 3. Crea una instancia del formulario con los datos de texto (request.POST)
        #    y los datos del archivo (request.FILES).
        form = ArchivoAdjuntoForm(request.POST, request.FILES)

        # 4. Valida el formulario.
        if form.is_valid():
            try:
                # 5. Si es válido, crea el objeto del modelo pero no lo guardes aún en la BD.
                archivo_adjunto = form.save(commit=False)
                # 6. Asigna la relación con el prospecto.
                archivo_adjunto.prospecto = prospecto
                # 7. Ahora guarda el objeto. Aquí es donde django-storages
                #    intentará subir el archivo a S3.
                archivo_adjunto.save()
                
                messages.success(request, "Archivo adjunto subido exitosamente.")

            except Exception as e:
                # 8. Si ocurre cualquier error durante el .save() (ej. un error de
                #    permisos de S3), lo captura y muestra en pantalla.
                messages.error(request, f"Error al contactar el servidor de archivos: {e}")
        else:
            # 9. Si el formulario no es válido, muestra los errores de validación.
            error_string = " ".join([f"{field}: {', '.join(errors)}" for field, errors in form.errors.items()])
            messages.error(request, f"Error en el formulario. Por favor, revisa los campos. Detalles: {error_string}")
            
    # 10. Redirige al usuario de vuelta a la página de detalles del prospecto.
    return redirect('prospecto-detail', pk=prospecto_pk)


@login_required
def delete_archivo(request, pk):
    archivo = get_object_or_404(ArchivoAdjunto, pk=pk)
    
    if archivo.prospecto.asignado_a != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("No tienes permiso para eliminar este archivo.")
    
    prospecto_pk = archivo.prospecto.pk
    file_name = archivo.nombre
    
    archivo.archivo.delete(save=False)
    archivo.delete()
    
    messages.success(request, f"El archivo '{file_name}' ha sido eliminado exitosamente.")
    return redirect('prospecto-detail', pk=prospecto_pk)