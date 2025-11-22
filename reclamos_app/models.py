from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Max
from django.db.models.functions import Substr, Cast
from django.db.models import IntegerField
import uuid
import os

def generar_numero_referencia():
    # Usamos la referencia al modelo a través de apps para evitar importación circular
    from django.apps import apps
    Reclamo = apps.get_model('reclamos_app', 'Reclamo')
    
    # Obtener el último número de referencia
    ultimo_reclamo = Reclamo.objects.filter(
        numero_referencia__startswith='INT-'
    ).annotate(
        numero=Cast(
            Substr('numero_referencia', 5),
            output_field=IntegerField()
        )
    ).aggregate(
        max_numero=Max('numero')
    )['max_numero']
    
    # Si no hay reclamos, empezar desde 1
    if ultimo_reclamo is None:
        siguiente_numero = 1
    else:
        siguiente_numero = ultimo_reclamo + 1
    
    # Formatear el número con ceros a la izquierda
    return f"INT-{siguiente_numero:05d}"

def archivo_reclamo_path(instance, filename):
    # Genera un path único para cada archivo
    ext = filename.split('.')[-1]
    filename = f"{instance.reclamo.numero_referencia}_{uuid.uuid4().hex[:10]}.{ext}"
    return os.path.join('archivos_reclamos', str(instance.reclamo.id), filename)

class Reclamo(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('EN_PROGRESO', 'En Progreso'),
        ('RESUELTO', 'Resuelto'),
        ('CERRADO', 'Cerrado'),
    ]

    titulo = models.CharField(max_length=200, verbose_name="Título")
    descripcion = models.TextField(verbose_name="Descripción")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='PENDIENTE',
        verbose_name="Estado"
    )
    cliente = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Cliente")
    numero_referencia = models.CharField(
        max_length=20, 
        unique=True,
        default=generar_numero_referencia,
        verbose_name="Número de Referencia"
    )
    prioridad = models.CharField(
        max_length=10,
        choices=[('BAJA', 'Baja'), ('MEDIA', 'Media'), ('ALTA', 'Alta')],
        default='MEDIA',
        verbose_name="Prioridad"
    )
    categoria = models.CharField(
        max_length=50,
        choices=[
            ('SERVICIO', 'Servicio'),
            ('FACTURACION', 'Facturación'),
            ('TECNICO', 'Técnico'),
            ('OTRO', 'Otro')
        ],
        default='OTRO',
        verbose_name="Categoría"
    )
    
    def __str__(self):
        return f"{self.numero_referencia} - {self.titulo}"

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = "Reclamo"
        verbose_name_plural = "Reclamos"

class Comentario(models.Model):
    reclamo = models.ForeignKey(Reclamo, on_delete=models.CASCADE, related_name='comentarios')
    autor = models.ForeignKey(User, on_delete=models.CASCADE)
    contenido = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    es_respuesta_oficial = models.BooleanField(default=False)

    class Meta:
        ordering = ['fecha']

class Notificacion(models.Model):
    TIPO_CHOICES = [
        ('ACTUALIZACION', 'Actualización de estado'),
        ('RESPUESTA', 'Respuesta recibida'),
        ('RECORDATORIO', 'Recordatorio'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    mensaje = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    leida = models.BooleanField(default=False)
    reclamo = models.ForeignKey(Reclamo, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-fecha']

class ArchivoReclamo(models.Model):
    reclamo = models.ForeignKey(Reclamo, on_delete=models.CASCADE, related_name='archivos')
    archivo = models.FileField(
        upload_to=archivo_reclamo_path,
        verbose_name="Archivo",
        help_text="Formatos permitidos: PDF, JPG, PNG"
    )
    nombre_original = models.CharField(max_length=255)
    tipo_archivo = models.CharField(max_length=100)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.reclamo.numero_referencia} - {self.nombre_original}"

    def extension(self):
        return os.path.splitext(self.archivo.name)[1].lower()

    def es_imagen(self):
        return self.extension() in ['.jpg', '.jpeg', '.png']

    def es_pdf(self):
        return self.extension() == '.pdf'

    class Meta:
        verbose_name = "Archivo de Reclamo"
        verbose_name_plural = "Archivos de Reclamos"
        ordering = ['-fecha_subida']
