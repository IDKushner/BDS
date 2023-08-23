from django.contrib import admin
from .models import *

class CouriersAdmin(admin.ModelAdmin):
    fields =  ['courier_type', 'regions', 'working_hours', 'orders']

    list_display = ['id'] + fields
    search_fields = fields
    list_editable = ['courier_type', 'regions', 'working_hours']
    list_filter = fields

class OrdersAdmin(admin.ModelAdmin):
    fields = ['weight', 'regions', 'cost', 'complete_time', 'courier']

    list_display = ['id'] + fields
    search_fields = fields
    list_editable = fields
    list_filter = fields

admin.site.register(Couriers, CouriersAdmin)
admin.site.register(Orders, OrdersAdmin)