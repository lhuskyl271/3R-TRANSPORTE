from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

# --- MODELO 'TRABAJADOR' DEFINIDO PRIMERO ---
class Trabajador(models.Model):
    nombre = models.CharField(max_length=150, verbose_name="Nombre del Trabajador")
    puesto = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True, verbose_name="Email")
    telefono = models.CharField(max_length=20, blank=True, verbose_name="Teléfono")

    # --- CORRECCIÓN 2: AÑADIR ORDENAMIENTO POR DEFECTO ---
    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return self.nombre
    
    def get_absolute_url(self):
        return reverse('trabajador-list')

# --- OTROS MODELOS INDEPENDIENTES ---
class Etiqueta(models.Model):
    nombre = models.CharField(max_length=50, unique=True, verbose_name="Nombre de Etiqueta")

    def __str__(self):
        return self.nombre

# --- MODELO 'PROSPECTO' QUE DEPENDE DE 'TRABAJADOR' ---
class Prospecto(models.Model):
    ESTADO_CHOICES = [
        ('NUEVO', 'Prospecto Inicial'),
        ('CONTACTADO', 'Primer Contacto'),
        ('CALIFICANDO', 'En Negociación'),
        ('GANADO', 'Cliente Cerrado'),
        ('PERDIDO', 'Rechazado'),
    ]

    INTERES_CHOICES = [
        ('IMPORTACION', 'Importación'),
        ('EXPORTACION', 'Exportación'),
        ('AMBOS', 'Ambos'),
        ('OTRO', 'Otro'),
    ]
    
    nombre_completo = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True)
    empresa = models.CharField(max_length=100, blank=True)
    puesto = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='NUEVO')
    etiquetas = models.ManyToManyField(Etiqueta, blank=True)
    
    referencio = models.CharField(max_length=150, blank=True, verbose_name="Referido por")
    contacto_referencio = models.CharField(max_length=150, blank=True, verbose_name="Contacto de Referencia")
    interes_principal = models.CharField(
        max_length=20, 
        choices=INTERES_CHOICES, 
        default='IMPORTACION', 
        verbose_name="Interés Principal"
    )
    
    interes_cliente = models.TextField(blank=True, verbose_name="Detalles del Interés del Cliente")
    
    trabajadores = models.ManyToManyField(
        Trabajador, 
        through='ProspectoTrabajador',
        related_name="prospectos", 
        verbose_name="Trabajadores de Contacto"
    )
    
    asignado_a = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='prospectos')
    
    # --- CORRECCIÓN 1: USAR timezone.now SIN PARÉNTESIS ---
    fecha_creacion = models.DateTimeField(default=timezone.now)
    
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    # --- CORRECCIÓN 2: AÑADIR ORDENAMIENTO POR DEFECTO ---
    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        return self.nombre_completo

    def get_absolute_url(self):
        return reverse('prospecto-detail', kwargs={'pk': self.pk})

    def get_estado_color(self):
        colores = {
            'NUEVO': 'secondary',
            'CONTACTADO': 'warning',
            'CALIFICANDO': 'primary',
            'GANADO': 'success',
            'PERDIDO': 'danger',
        }
        return colores.get(self.estado, 'light')

# --- MODELO INTERMEDIO QUE DEPENDE DE 'PROSPECTO' Y 'TRABAJADOR' ---
class ProspectoTrabajador(models.Model):
    CALIFICACION_CHOICES = [
        (1, '⭐ Malo'),
        (2, '⭐⭐ Regular'),
        (3, '⭐⭐⭐ Bueno'),
        (4, '⭐⭐⭐⭐ Muy Bueno'),
        (5, '⭐⭐⭐⭐⭐ Excelente'),
    ]

    prospecto = models.ForeignKey(Prospecto, on_delete=models.CASCADE)
    trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE, verbose_name="Trabajador")
    calificacion = models.IntegerField(choices=CALIFICACION_CHOICES, default=3, verbose_name="Calificación")

    class Meta:
        unique_together = ('prospecto', 'trabajador')

    def __str__(self):
        return f"{self.trabajador.nombre} en {self.prospecto.nombre_completo}"

# --- MODELOS RESTANTES ---
class Interaccion(models.Model):
    TIPO_CHOICES = [('LLAMADA', 'Llamada'), ('CORREO', 'Correo'), ('REUNION', 'Reunión'), ('OTRO', 'Otro')]
    prospecto = models.ForeignKey(Prospecto, on_delete=models.CASCADE, related_name='interacciones')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    
    # --- CORRECCIÓN 1: USAR timezone.now SIN PARÉNTESIS ---
    fecha = models.DateTimeField(default=timezone.now)
    
    notas = models.TextField()
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interacciones_creadas')
    
    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.get_tipo_display()} con {self.prospecto.nombre_completo}"

class Recordatorio(models.Model):
    prospecto = models.ForeignKey(Prospecto, on_delete=models.CASCADE, related_name='recordatorios')
    creado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recordatorios_creados')
    titulo = models.CharField(max_length=200)
    fecha_recordatorio = models.DateTimeField()
    completado = models.BooleanField(default=False)

    class Meta:
        ordering = ['-fecha_recordatorio']

    def __str__(self):
        return self.titulo