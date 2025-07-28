from django.db import models
from django.core.exceptions import ValidationError
import datetime

# Create your models here.
class Services(models.Model):
  name = models.CharField(max_length=100)
  description = models.TextField(blank=True)
  price = models.DecimalField(max_digits=8, decimal_places=2)
  duration_minutes= models.PositiveIntegerField(default=60) #Duracion en minutos

  def __str__(self):
    return self.name
  
class Booking(models.Model):
  STATUS_CHOICES = [
    ('active', 'Activa'),
    ('cancelled', 'Cancelada'),
    ('completed', 'Completada'),
  ]
  service = models.ForeignKey(Services, on_delete=models.CASCADE)
  custumer_name = models.CharField(max_length=100)
  custumer_phone = models.CharField(max_length=10)
  custumer_email = models.EmailField(null=True, blank=True)
  date = models.DateField()
  time = models.TimeField()
  created_at = models.DateTimeField(auto_now_add=True)
  end_time = models.TimeField(blank=True,null=True)
  status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

  
  #Evita que dos reservas tengan el mismo servicio, fecha y hora
  class Meta:
    unique_together = ('service', 'date', 'time')
    verbose_name = 'Reserva'
    verbose_name_plural = "Reservas"

  def save(self,*args, **kwargs):
    if self.service and self.time:
      start_datetime = datetime.datetime.combine(self.date, self.time)
      duration = datetime.timedelta(minutes=self.service.duration_minutes)
      end_datetime = start_datetime + duration
      self.end_time = end_datetime.time()
    super().save(*args, **kwargs)

  def __str__(self):
    return f"{self.custumer_name} - {self.service} - {self.date} {self.time}"
  
  def clean(self):
    #validar solo si hay fechas
    today = datetime.date.today()
    if self.date and self.date < datetime.date.today():
      raise ValidationError({"date": "⚠️No puedes reservar en una fecha pasada"})
    
    #solo varidar horas si tienen un rango permitido
    if self.time:
      opening = datetime.time(8, 0)
      closing =  datetime.time(19, 0)
      if self.time < opening or self.time > closing:
        raise ValidationError("⚠️ La hora debe estar entre 08:00 y 19:00")
    

  def __str__(self):
    return f"{self.custumer_name} - {self.service.name} ({self.date} {self.time})"