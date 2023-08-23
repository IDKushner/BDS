from django.db import models
from django.contrib.postgres.fields import ArrayField

CHOICES = (
    ('FOOT', 'FOOT'),
    ('BIKE', 'BIKE'),
    ('AUTO', 'AUTO')
)

class Couriers(models.Model):
    courier_type = models.CharField(max_length=10, choices=CHOICES)
    regions = ArrayField(models.IntegerField())
    working_hours = ArrayField(models.CharField(max_length=11))

    class Meta:
        ordering = ['id', 'courier_type', 'regions', 'working_hours']
        verbose_name_plural = 'Couriers'

    def __str__(self):
        return f'Курьер № {self.pk}'

class Orders(models.Model):
    assignment_date = models.DateField(null=True)
    weight = models.FloatField()
    regions = models.IntegerField()
    delivery_hours = ArrayField(models.CharField(max_length=11))
    cost = models.IntegerField()
    complete_time = models.DateTimeField(null=True)
    courier = models.ForeignKey(Couriers, related_name='orders', 
                                on_delete=models.PROTECT, default=None, null=True)

    class Meta:
        ordering = ['id', 'weight', 'regions', 'cost', 'complete_time', 'courier']
        verbose_name_plural = 'Orders'

    def __str__(self):
        return f'Заказ № {self.pk}'