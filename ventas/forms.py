from django import forms
from .models import Prospecto, Interaccion, Recordatorio, Trabajador, ProspectoTrabajador

class ProspectoForm(forms.ModelForm):
    class Meta:
        model = Prospecto
        # --- CAMPOS ACTUALIZADOS ---
        # Quitamos 'calificacion' y 'trabajadores' de aquí
        fields = [
            'nombre_completo', 'email', 'telefono', 'empresa', 'puesto', 'estado', 
            'interes_principal', 'referencio', 'contacto_referencio', 
            'interes_cliente'
        ]
        widgets = {
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'empresa': forms.TextInput(attrs={'class': 'form-control'}),
            'puesto': forms.TextInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
            'interes_principal': forms.Select(attrs={'class': 'form-select'}),
            'referencio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Cliente Actual, Evento, etc.'}),
            'contacto_referencio': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Nombre o email del contacto'}),
            'interes_cliente': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe los productos o servicios de interés...'}),
        }

# --- NUEVO FORMULARIO PARA ASIGNAR TRABAJADOR Y CALIFICACIÓN ---
class ProspectoTrabajadorForm(forms.ModelForm):
    class Meta:
        model = ProspectoTrabajador
        fields = ['trabajador', 'calificacion']
        widgets = {
            'trabajador': forms.Select(attrs={'class': 'form-select mb-2'}),
            # ✅ Mantener RadioSelect pero asegurar que se renderice correctamente
            'calificacion': forms.RadioSelect(attrs={'class': 'form-check-input'}), 
        }
    
    # ✅ Añadir esta función para forzar la validación del campo calificacion
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['calificacion'].required = True


# ... (El resto de los formularios: TrabajadorForm, InteraccionForm, etc. se quedan igual)
class TrabajadorForm(forms.ModelForm):
    class Meta:
        model = Trabajador
        fields = ['nombre', 'puesto', 'email', 'telefono']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'puesto': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
class InteraccionForm(forms.ModelForm):
    class Meta:
        model = Interaccion
        fields = ['tipo', 'notas']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-select mb-2'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe la interacción...'}),
        }

class RecordatorioForm(forms.ModelForm):
    class Meta:
        model = Recordatorio
        fields = ['titulo', 'fecha_recordatorio']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control mb-2', 'placeholder': 'Título del recordatorio'}),
            'fecha_recordatorio': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }