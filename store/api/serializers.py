from rest_framework import serializers
from .models import CHOICES, Couriers, Orders


class IntegerListField(serializers.ListField):
    child = serializers.CharField()


class StringListField(serializers.ListField):
    child = serializers.CharField()


class CouriersSerializer(serializers.ModelSerializer):
    courier_type = serializers.ChoiceField(choices=CHOICES)
    regions = IntegerListField()
    working_hours = StringListField()

    class Meta:
        model = Couriers
        fields = ('id', 'courier_type', 'regions', 'working_hours')

class OrdersSerializer(serializers.ModelSerializer):
    delivery_hours = StringListField()

    class Meta:
        model = Orders
        fields = ('id', 'weight', 'regions', 'delivery_hours', 'cost')

class CompleteOrderSerializer(serializers.Serializer):
    courier_id = serializers.IntegerField()
    order_id = serializers.IntegerField()
    complete_time = serializers.DateTimeField()

    class Meta:
        model = Orders
        fields = ('id', 'weight', 'regions', 'cost', 'complete_time', 'courier')

    def validate(self, data):
        courier_id = data.get('courier_id')
        order_id = data.get('order_id')
        complete_time = data.get('complete_time') 

        try:
            order = Orders.objects.get(pk=order_id)
        except Orders.DoesNotExist:
            raise serializers.ValidationError('Order does not exist')

        if order.courier_id is None or order.courier_id != courier_id:
            raise serializers.ValidationError('Order was not assigned to this courier')

        data['order'] = order
        data['courier'] = order.courier
        data['complete_time'] = complete_time

        return data