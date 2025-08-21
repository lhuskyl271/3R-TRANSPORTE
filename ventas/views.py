from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy, reverse
from .models import Prospecto, Interaccion, Recordatorio, Etiqueta, Trabajador, ProspectoTrabajador
from .forms import (
    ProspectoForm, InteraccionForm, RecordatorioForm, TrabajadorForm, ProspectoTrabajadorForm, ProspectoTrabajadorUpdateForm 
)
from django.db.models import Count, Q, Avg, Max
from django.http import HttpResponseForbidden, HttpResponse
import datetime
from openpyxl import Workbook
from django.contrib import messages # 👈 Asegúrate que messages esté importado al inicio del archivo

from openpyxl.styles import Font, Alignment
from django.utils import timezone
import json # Import json for chart data

from datetime import timedelta



# Mixin para verificar que el usuario es dueño del objeto
class OwnerRequiredMixin:
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        
        # El objeto puede ser Prospecto, Interaccion o Recordatorio
        if isinstance(obj, Prospecto):
            asignado = obj.asignado_a
        elif isinstance(obj, (Interaccion, Recordatorio)):
            asignado = obj.prospecto.asignado_a
        else:
            # Para otros modelos como Trabajador, no restringimos por ahora
            return obj

        if asignado != self.request.user and not self.request.user.is_superuser:
            raise HttpResponseForbidden("No tienes permiso para realizar esta acción.")
        return obj

# --- VISTAS DE TRABAJADORES ---

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


# --- VISTAS PARA EDITAR/ELIMINAR INTERACCIONES ---

class InteraccionUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = Interaccion
    form_class = InteraccionForm
    template_name = 'ventas/interaccion_form.html'

    def get_success_url(self):
        return reverse('prospecto-detail', kwargs={'pk': self.object.prospecto.pk})

class InteraccionDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Interaccion
    template_name = 'ventas/interaccion_confirm_delete.html'
    
    def get_success_url(self):
        return reverse('prospecto-detail', kwargs={'pk': self.object.prospecto.pk})


# --- VISTAS PARA EDITAR/ELIMINAR RECORDATORIOS ---

class RecordatorioUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = Recordatorio
    form_class = RecordatorioForm
    template_name = 'ventas/recordatorio_form.html'

    def get_success_url(self):
        return reverse('prospecto-detail', kwargs={'pk': self.object.prospecto.pk})

class RecordatorioDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Recordatorio
    template_name = 'ventas/recordatorio_confirm_delete.html'
    
    def get_success_url(self):
        return reverse('prospecto-detail', kwargs={'pk': self.object.prospecto.pk})


# --- VISTAS EXISTENTES (con las modificaciones necesarias) ---
# ... (DashboardView, ProspectoListView, ProspectoDetailView, etc. se mantienen como las tenías)
# ... (No es necesario volver a pegarlas si no cambian)
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'ventas/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        prospectos_qs = Prospecto.objects.filter(asignado_a=user) if not user.is_superuser else Prospecto.objects.all()

        context['total_prospectos'] = prospectos_qs.count()
        context['prospectos_nuevos'] = prospectos_qs.filter(estado='NUEVO').count()
        context['clientes_ganados'] = prospectos_qs.filter(estado='GANADO').count()
        
        reporte_data = prospectos_qs.values('estado').annotate(total=Count('estado')).order_by('estado')
        
        # --- ✅ CORRECCIÓN AQUÍ ---
        # Usamos la nueva clase `Estado` del modelo Prospecto para obtener los nombres
        estado_display_map = dict(Prospecto.Estado.choices) 
        
        chart_data = {
            "labels": [estado_display_map.get(item['estado'], item['estado']) for item in reporte_data],
            "data": [item['total'] for item in reporte_data],
        }
        context['chart_data_json'] = json.dumps(chart_data)
        
        # ... (el resto de la vista se mantiene igual) ...
        promedio_calificaciones = ProspectoTrabajador.objects.filter(
            prospecto__in=prospectos_qs
        ).values(
            'trabajador__nombre'
        ).annotate(
            promedio=Avg('calificacion')
        ).order_by('-promedio')
        
        context['promedio_calificaciones_trabajador'] = promedio_calificaciones

        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        prospectos_activos_ids = Interaccion.objects.filter(
            prospecto__in=prospectos_qs,
            fecha__gte=thirty_days_ago
        ).values_list('prospecto_id', flat=True).distinct()

        prospectos_inactivos = prospectos_qs.exclude(
            Q(estado__in=['GANADO', 'PERDIDO']) | Q(id__in=prospectos_activos_ids)
        ).annotate(
            ultima_interaccion=Max('interacciones__fecha')
        ).filter(
            Q(ultima_interaccion__lt=thirty_days_ago) | Q(ultima_interaccion__isnull=True, fecha_creacion__lt=thirty_days_ago)
        ).order_by('ultima_interaccion')

        context['prospectos_inactivos'] = prospectos_inactivos
        context['seguimiento_requerido_count'] = prospectos_inactivos.count()

        hoy = timezone.now()
        quince_dias_despues = hoy + timedelta(days=15)
        
        recordatorios_proximos = Recordatorio.objects.filter(
            prospecto__in=prospectos_qs,
            completado=False,
            fecha_recordatorio__gte=hoy,
            fecha_recordatorio__lte=quince_dias_despues
        ).select_related('prospecto').order_by('fecha_recordatorio')

        context['recordatorios_proximos'] = recordatorios_proximos
        
        return context


class ProspectoListView(LoginRequiredMixin, ListView):
    model = Prospecto
    template_name = 'ventas/prospecto_list.html'
    context_object_name = 'prospectos'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        if not user.is_superuser:
            queryset = super().get_queryset().filter(asignado_a=user)
        else:
            queryset = super().get_queryset()

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
        
        # Usamos el queryset base de la vista para los conteos, respetando permisos
        base_qs = self.get_queryset().model.objects.all()
        if not self.request.user.is_superuser:
            base_qs = base_qs.filter(asignado_a=self.request.user)

        status_counts_dict = {
            item['estado']: item['total'] 
            for item in base_qs.values('estado').annotate(total=Count('id'))
        }

        status_cards_data = []
        # --- ✅ CORRECCIÓN AQUÍ ---
        # Iteramos sobre la nueva clase `Estado.choices`
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
        
        # --- NUEVO FORMULARIO PARA AÑADIR TRABAJADOR ---
        context['trabajador_form'] = ProspectoTrabajadorForm()
        
        # Obtenemos los trabajadores ya asociados para excluirlos del select
        trabajadores_asociados_ids = self.object.trabajadores.values_list('id', flat=True)
        context['trabajador_form'].fields['trabajador'].queryset = Trabajador.objects.exclude(id__in=trabajadores_asociados_ids)
        
        # Pasamos las relaciones a la plantilla
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
        return super().form_valid(form)

class ProspectoUpdateView(LoginRequiredMixin, OwnerRequiredMixin, UpdateView):
    model = Prospecto
    form_class = ProspectoForm
    template_name = 'ventas/prospecto_form.html'

class ProspectoDeleteView(LoginRequiredMixin, OwnerRequiredMixin, DeleteView):
    model = Prospecto
    template_name = 'ventas/prospecto_confirm_delete.html'
    success_url = reverse_lazy('prospecto-list')

@login_required
def add_interaccion(request, prospecto_pk):
    prospecto = get_object_or_404(Prospecto, pk=prospecto_pk)
    if prospecto.asignado_a != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("No tienes permiso.")
    
    if request.method == 'POST':
        form = InteraccionForm(request.POST)
        if form.is_valid():
            interaccion = form.save(commit=False)
            interaccion.prospecto = prospecto
            interaccion.creado_por = request.user
            interaccion.save()
    return redirect('prospecto-detail', pk=prospecto_pk)

@login_required
def add_recordatorio(request, prospecto_pk):
    prospecto = get_object_or_404(Prospecto, pk=prospecto_pk)
    if prospecto.asignado_a != request.user and not request.user.is_superuser:
        return HttpResponseForbidden("No tienes permiso.")

    if request.method == 'POST':
        form = RecordatorioForm(request.POST)
        if form.is_valid():
            recordatorio = form.save(commit=False)
            recordatorio.prospecto = prospecto
            recordatorio.creado_por = request.user
            recordatorio.save()
    return redirect('prospecto-detail', pk=prospecto_pk)

@login_required
def toggle_recordatorio(request, pk):
    recordatorio = get_object_or_404(Recordatorio, pk=pk)
    if recordatorio.creado_por != request.user and (recordatorio.prospecto.asignado_a != request.user and not request.user.is_superuser):
        return HttpResponseForbidden("No tienes permiso.")
        
    recordatorio.completado = not recordatorio.completado
    recordatorio.save()
    return redirect('prospecto-detail', pk=recordatorio.prospecto.pk)


@login_required
def export_prospectos_excel(request):
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    response['Content-Disposition'] = f'attachment; filename="prospectos_{timestamp}.xlsx"'

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'Prospectos'

    # --- ENCABEZADOS ACTUALIZADOS ---
    headers = [
        'Nombre Completo', 'Email', 'Teléfono', 'Empresa', 'Puesto', 'Estado', 
        'Interés Principal', 'Calificación', 'Referido Por', 'Contacto Referencia',
        'Detalle Interés', 'Trabajadores', 'Etiquetas', 'Asignado a', 'Fecha de Creación'
    ]
    for col_num, header_title in enumerate(headers, 1):
        cell = worksheet.cell(row=1, column=col_num, value=header_title)
        cell.font = Font(bold=True, name='Calibri', size=12)
        cell.alignment = Alignment(horizontal='center', vertical='center')

    if request.user.is_superuser:
        prospectos = Prospecto.objects.all().select_related('asignado_a').prefetch_related('etiquetas', 'trabajadores')
    else:
        prospectos = Prospecto.objects.filter(asignado_a=request.user).select_related('asignado_a').prefetch_related('etiquetas', 'trabajadores')

    for row_num, prospecto in enumerate(prospectos, 2):
        etiquetas_str = ", ".join([etiqueta.nombre for etiqueta in prospecto.etiquetas.all()])
        trabajadores_str = ", ".join([t.nombre for t in prospecto.trabajadores.all()])
        
        row_data = [
            prospecto.nombre_completo,
            prospecto.email,
            prospecto.telefono,
            prospecto.empresa,
            prospecto.puesto,
            prospecto.get_estado_display(),
            prospecto.get_interes_principal_display(),
            prospecto.get_calificacion_display(),
            prospecto.referencio,
            prospecto.contacto_referencio,
            prospecto.interes_cliente,
            trabajadores_str,
            etiquetas_str,
            prospecto.asignado_a.username if prospecto.asignado_a else 'No asignado',
            prospecto.fecha_creacion.strftime('%Y-%m-%d %H:%M')
        ]
        for col_num, cell_value in enumerate(row_data, 1):
            worksheet.cell(row=row_num, column=col_num, value=cell_value)

    for i, column_cells in enumerate(worksheet.columns):
        try:
            max_length = 0
            column = chr(65 + i)
            for cell in column_cells:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            adjusted_width = (max_length + 2)
            worksheet.column_dimensions[column].width = adjusted_width
        except:
            pass

    workbook.save(response)
    return response

@login_required
def add_trabajador_a_prospecto(request, prospecto_pk):
    prospecto = get_object_or_404(Prospecto, pk=prospecto_pk)

    if request.method == 'POST':
        form = ProspectoTrabajadorForm(request.POST)
        if form.is_valid():
            # Verificar si ya existe esta relación
            trabajador = form.cleaned_data['trabajador']
            if ProspectoTrabajador.objects.filter(prospecto=prospecto, trabajador=trabajador).exists():
                messages.error(request, f"Este empleado ya está asignado al prospecto.")
            else:
                relacion = form.save(commit=False)
                relacion.prospecto = prospecto
                relacion.save()
                messages.success(request, f"¡El empleado '{relacion.trabajador}' fue asignado correctamente!")
        else:
            # Mostrar errores de validación al usuario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"Error en {field}: {error}")
    
    return redirect('prospecto-detail', pk=prospecto_pk)

class ProspectoTrabajadorUpdateView(LoginRequiredMixin, UpdateView):
    model = ProspectoTrabajador
    form_class = ProspectoTrabajadorUpdateForm # <= USA EL NUEVO FORMULARIO
    template_name = 'ventas/prospecto_trabajador_form.html'

    def get_success_url(self):
        messages.success(self.request, f"Se actualizó la calificación para el trabajador '{self.object.trabajador.nombre}'.")
        return reverse('prospecto-detail', kwargs={'pk': self.object.prospecto.pk})


class ProspectoTrabajadorDeleteView(LoginRequiredMixin, DeleteView):
    # ... (esta vista se queda igual) ...
    model = ProspectoTrabajador
    template_name = 'ventas/prospecto_trabajador_confirm_delete.html'
    
    def get_success_url(self):
        return reverse('prospecto-detail', kwargs={'pk': self.object.prospecto.pk})
