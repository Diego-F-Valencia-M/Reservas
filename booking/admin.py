from django.contrib import admin
from .models import Services, Booking

# Register your models here.
admin.site.register(Services)
@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
  list_display = ("custumer_name", "service", "date", "time", "end_time", "status")
  list_filter = ("status", "date", "service")
  actions = ["marcar_como_cancelada"]

  def marcar_como_cancelada(self, request, queryset):
    updated = queryset.update(status = "cancelle")
    self.message_user(request, f"{updated} reservvas marcadas como canceladas.")
  marcar_como_cancelada.short_description = "❌ arcar como canceladas"