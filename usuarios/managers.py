from django.db import models

class SedeFilteredManager(models.Manager):
    """
    Manager que filtra automáticamente por la sede del usuario autenticado.
    Para usarlo, el modelo debe tener un campo 'sede' que sea ForeignKey a Sede.
    """
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Intentar obtener la sede del contexto actual
        try:
            # Esto se usará cuando se llame desde una vista con request
            from django.contrib.auth.middleware import get_user
            from threading import local
            
            thread_local = local()
            if hasattr(thread_local, 'sede_id'):
                return queryset.filter(sede_id=thread_local.sede_id)
        except:
            pass
            
        return queryset
    
    def for_sede(self, sede):
        """
        Método explícito para filtrar por una sede específica
        """
        return self.get_queryset().filter(sede=sede)

class CitaManager(SedeFilteredManager):
    """
    Manager específico para el modelo Cita con filtrado por sede
    """
    
    def for_sede(self, sede):
        return super().for_sede(sede)
    
    def pendientes(self, sede=None):
        """
        Obtener citas pendientes para una sede específica
        """
        queryset = self.get_queryset().filter(estado='pendiente')
        if sede:
            queryset = queryset.filter(sede=sede)
        return queryset
    
    def confirmadas(self, sede=None):
        """
        Obtener citas confirmadas para una sede específica
        """
        queryset = self.get_queryset().filter(estado='confirmada')
        if sede:
            queryset = queryset.filter(sede=sede)
        return queryset
    
    def del_dia(self, sede=None, fecha=None):
        """
        Obtener citas del día para una sede específica
        """
        from django.utils import timezone
        from datetime import date
        
        if fecha is None:
            fecha = timezone.now().date()
        
        queryset = self.get_queryset().filter(
            fecha_hora__date=fecha
        )
        if sede:
            queryset = queryset.filter(sede=sede)
        return queryset
