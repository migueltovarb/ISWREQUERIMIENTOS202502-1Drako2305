from django.contrib import admin
from .models import Reclamo

@admin.register(Reclamo)
class ReclamoAdmin(admin.ModelAdmin):
    list_display = ['numero_referencia', 'titulo', 'cliente', 'estado', 'fecha_creacion']
    list_filter = ['estado', 'fecha_creacion']
    search_fields = ['numero_referencia', 'titulo', 'descripcion', 'cliente__username']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    ordering = ['-fecha_creacion']
