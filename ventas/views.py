from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from .models import Prospecto, Interaccion, Recordatorio, Etiqueta, Trabajador, ProspectoTrabajador
from .forms import (
    ProspectoForm, InteraccionForm, RecordatorioForm, TrabajadorForm, 
    ProspectoTrabajadorForm, ProspectoTrabajadorUpdateForm
)
from django.db.models import Count, Q, Avg, Max
from django.http import HttpResponseForbidden, HttpResponse
from openpyxl import Workbook
from django.contrib import messages
from openpyxl.styles import Font, Alignment
from django.utils import timezone
import json
from datetime import timedelta
import pytz 

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
        elif isinstance(obj, (Interaccion, Recordatorio, ProspectoTrabajador)):
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
    
    # --- AJUSTE DE ZONA HORARIA PARA MÉXICO ---
    try:
        user_timezone = pytz.timezone('America/Mexico_City') 
    except pytz.UnknownTimeZoneError:
        user_timezone = pytz.timezone(timezone.get_default_timezone_name())

    hoy = timezone.now().astimezone(user_timezone)
    
    # --- QUERIES PARA LOS DATOS DEL DASHBOARD ---

    # Filtro base de prospectos según el tipo de usuario.
    prospectos_qs = Prospecto.objects.all()
    if not user.is_superuser:
        prospectos_qs = prospectos_qs.filter(asignado_a=user)

    # KPIs principales.
    context['total_prospectos'] = prospectos_qs.count()
    
    # Prospectos nuevos (menos de 15 días)
    quince_dias_atras = hoy - timedelta(days=15)
    context['prospectos_nuevos'] = prospectos_qs.filter(
        estado=Prospecto.Estado.NUEVO,
        fecha_creacion__gte=quince_dias_atras
    ).count()
    
    context['clientes_ganados'] = prospectos_qs.filter(estado=Prospecto.Estado.GANADO).count()
    
    # Datos para el gráfico de pastel.
    reporte_data = prospectos_qs.values('estado').annotate(total=Count('estado')).order_by('estado')
    estado_display_map = dict(Prospecto.Estado.choices) 
    chart_data = {
        "labels": [estado_display_map.get(item['estado'], item['estado']) for item in reporte_data],
        "data": [item['total'] for item in reporte_data],
    }
    context['chart_data_json'] = json.dumps(chart_data)
    
    # Calificación promedio por trabajador.
    promedio_calificaciones = ProspectoTrabajador.objects.filter(
        prospecto__in=prospectos_qs
    ).values('trabajador__nombre').annotate(promedio=Avg('calificacion')).order_by('-promedio')
    context['promedio_calificaciones_trabajador'] = promedio_calificaciones

    # Prospectos inactivos que requieren seguimiento.
    thirty_days_ago = hoy - timedelta(days=30)
    prospectos_activos_ids = Interaccion.objects.filter(
        prospecto__in=prospectos_qs, fecha__gte=thirty_days_ago
    ).values_list('prospecto_id', flat=True).distinct()

    prospectos_inactivos = prospectos_qs.exclude(
        Q(estado__in=[Prospecto.Estado.GANADO, Prospecto.Estado.PERDIDO]) | Q(id__in=prospectos_activos_ids)
    ).annotate(
        ultima_interaccion=Max('interacciones__fecha')
    ).filter(
        Q(ultima_interaccion__lt=thirty_days_ago) | Q(ultima_interaccion__isnull=True, fecha_creacion__lt=thirty_days_ago)
    ).order_by('ultima_interaccion')
    
    context['prospectos_inactivos'] = prospectos_inactivos
    context['seguimiento_requerido_count'] = prospectos_inactivos.count()

    # Recordatorios próximos (usando la hora local correcta).
    quince_dias_despues = hoy + timedelta(days=15)
    recordatorios_proximos = Recordatorio.objects.filter(
        prospecto__in=prospectos_qs, completado=False, 
        fecha_recordatorio__gte=hoy, fecha_recordatorio__lte=quince_dias_despues
    ).select_related('prospecto').order_by('fecha_recordatorio')
    context['recordatorios_proximos'] = recordatorios_proximos
    
    # Recordatorios pasados (no completados y con fecha anterior a hoy)
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
        # ✅ CORRECCIÓN: Usar la clase interna `Estado.choices` del modelo.
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

# ==============================================================================
# VISTAS DE TRABAJADORES (CRUD)
# ==============================================================================

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

# ==============================================================================
# VISTAS DE RELACIÓN (PROSPECTO <-> TRABAJADOR)
# ==============================================================================

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

# ==============================================================================
# VISTAS DE ACTIVIDADES (INTERACCIONES Y RECORDATORIOS)
# ==============================================================================

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
    # OwnerRequiredMixin no aplica a funciones, así que validamos manualmente
    if recordatorio.prospecto.asignado_a != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("No tienes permiso.")
    
    recordatorio.completado = not recordatorio.completado
    recordatorio.save()
    status = "completado" if recordatorio.completado else "marcado como pendiente"
    messages.info(request, f"Recordatorio '{recordatorio.titulo}' {status}.")
    return redirect('prospecto-detail', pk=recordatorio.prospecto.pk)

# ==============================================================================
# VISTA DE EXPORTACIÓN
# ==============================================================================

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
