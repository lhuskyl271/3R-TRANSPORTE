from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.core.validators import RegexValidator


# --- Validadores ---
# Validador para asegurar un formato de teléfono básico.
phone_validator = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="El número de teléfono debe tener el formato: '+999999999'. Hasta 15 dígitos permitidos."
)

# ==============================================================================
# 1. MODELOS PRINCIPALES
# ==============================================================================

class Trabajador(models.Model):
    """Representa a un empleado o contacto de una empresa cliente."""
    nombre = models.CharField(max_length=150, verbose_name="Nombre del Trabajador")
    puesto = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True, verbose_name="Email")
    telefono = models.CharField(
        validators=[phone_validator],
        max_length=17,
        blank=True,
        verbose_name="Teléfono",
        help_text="Formato: +521234567890"
    )

    class Meta:
        ordering = ['nombre']
        verbose_name = "Trabajador"
        verbose_name_plural = "Trabajadores"

    def __str__(self):
        return self.nombre
    
    def get_absolute_url(self):
        return reverse('trabajador-list')

class Etiqueta(models.Model):
    """Permite categorizar prospectos (ej. 'Industria Automotriz', 'Cliente VIP')."""
    nombre = models.CharField(max_length=50, unique=True, verbose_name="Nombre de Etiqueta")

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Prospecto(models.Model):
    """El modelo central. Contiene toda la información de un cliente potencial."""

    # ✅ MEJORA: Uso de TextChoices para los estados. Más legible y moderno.
    class Estado(models.TextChoices):
        NUEVO = 'NUEVO', 'Prospecto Inicial'
        CONTACTADO = 'CONTACTADO', 'Primer Contacto'
        CALIFICANDO = 'CALIFICANDO', 'En Negociación'
        GANADO = 'GANADO', 'Cliente Cerrado'
        PERDIDO = 'PERDIDO', 'Rechazado'

    class Interes(models.TextChoices):
        IMPORTACION = 'IMPORTACION', 'Importación'
        EXPORTACION = 'EXPORTACION', 'Exportación'
        AMBOS = 'AMBOS', 'Ambos'
        OTRO = 'OTRO', 'Otro'
    
    nombre_completo = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    telefono = models.CharField(
        max_length=25,  # Aumentamos un poco por si acaso
        blank=True,     # Opcional: permite que el campo esté vacío
        help_text="Introduce el número de teléfono con código de país, ej: +1 (555) 123-4567"
    )

    empresa = models.CharField(max_length=100, blank=True)
    puesto = models.CharField(max_length=100, blank=True)
    
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.NUEVO
    )
    
    interes_principal = models.CharField(
        max_length=20, 
        choices=Interes.choices, 
        default=Interes.IMPORTACION, 
        verbose_name="Interés Principal"
    )
    
    referencio = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Referido por",
        help_text="¿Cómo llegó este prospecto a nosotros? (ej: 'Cliente X', 'Evento Y')"
    )
    
    contacto_referencio = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Contacto de Referencia",
        help_text="Persona específica que lo refirió."
    )
    
    interes_cliente = models.TextField(
        blank=True,
        verbose_name="Detalles del Interés del Cliente",
        help_text="Describe los productos o servicios de interés del prospecto."
    )
    
    etiquetas = models.ManyToManyField(Etiqueta, blank=True)
    trabajadores = models.ManyToManyField(
        Trabajador, 
        through='ProspectoTrabajador',
        related_name="prospectos", 
        verbose_name="Trabajadores de Contacto"
    )
    
    asignado_a = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='prospectos')
    
    fecha_creacion = models.DateTimeField(default=timezone.now)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.nombre_completo

    def get_absolute_url(self):
        return reverse('prospecto-detail', kwargs={'pk': self.pk})

    def get_estado_color(self):
        colores = {
            self.Estado.NUEVO: 'secondary',
            self.Estado.CONTACTADO: 'warning',
            self.Estado.CALIFICANDO: 'primary',
            self.Estado.GANADO: 'success',
            self.Estado.PERDIDO: 'danger',
        }
        return colores.get(self.estado, 'light')

# ==============================================================================
# 2. MODELOS DE RELACIÓN (TABLAS INTERMEDIAS)
# ==============================================================================

class ProspectoTrabajador(models.Model):
    """Modelo intermedio que conecta Prospecto y Trabajador, añadiendo una calificación."""
    
    # ✅ MEJORA: Uso de IntegerChoices para las calificaciones.
    class Calificacion(models.IntegerChoices):
        MALO = 1, '⭐ Malo'
        REGULAR = 2, '⭐⭐ Regular'
        BUENO = 3, '⭐⭐⭐ Bueno'
        MUY_BUENO = 4, '⭐⭐⭐⭐ Muy Bueno'
        EXCELENTE = 5, '⭐⭐⭐⭐⭐ Excelente'

    prospecto = models.ForeignKey(Prospecto, on_delete=models.CASCADE)
    trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE, verbose_name="Trabajador")
    calificacion = models.IntegerField(
        choices=Calificacion.choices,
        default=Calificacion.BUENO,
        verbose_name="Calificación"
    )

    class Meta:
        unique_together = ('prospecto', 'trabajador')
        ordering = ['prospecto', 'trabajador']

    def __str__(self):
        return f"{self.trabajador.nombre} en {self.prospecto.nombre_completo}"

# ==============================================================================
# 3. MODELOS DE ACTIVIDAD
# ==============================================================================

class Interaccion(models.Model):
    """Registra cada punto de contacto con un prospecto (llamada, correo, etc.)."""
    
    class Tipo(models.TextChoices):
        LLAMADA = 'LLAMADA', 'Llamada'
        CORREO = 'CORREO', 'Correo'
        REUNION = 'REUNION', 'Reunión'
        OTRO = 'OTRO', 'Otro'
        
    prospecto = models.ForeignKey(Prospecto, on_delete=models.CASCADE, related_name='interacciones')
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    fecha = models.DateTimeField(default=timezone.now)
    notas = models.TextField()
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interacciones_creadas')
    
    class Meta:
        ordering = ['-fecha']
        verbose_name = "Interacción"
        verbose_name_plural = "Interacciones"

    def __str__(self):
        return f"{self.get_tipo_display()} con {self.prospecto.nombre_completo}"

class Recordatorio(models.Model):
    """Permite crear recordatorios o tareas de seguimiento para un prospecto."""
    prospecto = models.ForeignKey(Prospecto, on_delete=models.CASCADE, related_name='recordatorios')
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recordatorios_creados')
    titulo = models.CharField(max_length=200)
    fecha_recordatorio = models.DateTimeField()
    completado = models.BooleanField(default=False)

    class Meta:
        ordering = ['-fecha_recordatorio']

    def __str__(self):
        return self.titulo
    
class ArchivoAdjunto(models.Model):
    """Permite adjuntar archivos a un prospecto."""
    prospecto = models.ForeignKey(
        'Prospecto', 
        on_delete=models.CASCADE, 
        related_name='archivos_adjuntos'
    )
    nombre = models.CharField(max_length=255, verbose_name="Título del Archivo")
    
    # --- LÍNEA CORREGIDA ---
    # Se especifica un directorio para organizar los archivos.
    # Puedes usar %Y/%m/ para organizar por año y mes automáticamente.
    archivo = models.FileField(
        upload_to='archivos_adjuntos/%Y/%m/', 
        verbose_name="Archivo Adjunto"
    )
    
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_subida']
        verbose_name = "Archivo Adjunto"
        verbose_name_plural = "Archivos Adjuntos"

    def __str__(self):
        return self.nombre
    
