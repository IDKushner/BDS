import datetime
from django.db.models import Q, Count
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response
from .models import Couriers, Orders
from .serializers import CouriersSerializer, OrdersSerializer, CompleteOrderSerializer

class CustomPagination(LimitOffsetPagination):
    default_limit = 1
    default_offset = 0
    field = 'field'

    def get_paginated_response(self, data, field):
        result = {
                'count': self.count,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'offset': self.offset,
                'limit': self.limit,
                field: data
                }

        return Response(result)

class CouriersPagination(CustomPagination):
    def get_paginated_response(self, data):
        return super().get_paginated_response(data, field='couriers')

class OrdersPagination(CustomPagination):
    def get_paginated_response(self, data):
        return super().get_paginated_response(data, field='orders')

class StoreViewSet(mixins.CreateModelMixin, mixins.RetrieveModelMixin, 
                     mixins.ListModelMixin, viewsets.GenericViewSet):
    pass

class CouriersViewSet(StoreViewSet):
    queryset = Couriers.objects.all()
    serializer_class = CouriersSerializer
    pagination_class = CouriersPagination

    def create(self, request, *args, **kwargs):
        serializer = CouriersSerializer(data=request.data['content']['couriers'], many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        response_data = {
            'couriers': serializer.data
        }

        return Response(response_data, status=status.HTTP_200_OK)


    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'content': serializer.data})

    @action(detail=True, methods=['GET'], url_path='meta-info/<int:courier_id>')    
    def get_meta_info(self, request, courier_id):
        start_date = request.query_params.get('startDate')
        end_date = request.query_params.get('endDate')
        if not start_date or not end_date:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            courier = Couriers.objects.get(pk=courier_id) 
        except:
            return Response(status=status.HTTP_404_NOT_FOUND)
        
        orders = courier.orders.filter(
            complete_time__range=(start_date, end_date)
            )
        
        # расчёт рейтинга
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        rating_period = end_date-start_date
        rating_coefs = {'FOOT':3 , 'BIKE':2, 'AUTO':1}
        rating = (
            (len(orders)/(rating_period.days*24)) * rating_coefs[courier.courier_type]
        )

        # расчет заработка
        earnings_coefs = {'FOOT':2 , 'BIKE':3, 'AUTO':4}
        earnings = sum(
            [order.cost * earnings_coefs[courier.courier_type] 
             for order in orders]
        )        

        response_data = {
            'content': {
                'courier_id': courier.id,
                'courier_type':courier.courier_type,
                'regions':courier.regions,
                'working_hours':courier.working_hours
            }
        }

        if rating:
            response_data['content']['rating'] = rating

        if earnings:
            response_data['content']['earnings'] = earnings

        return Response(response_data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['GET'], url_path='assignments')
    def get_assigned_orders(self, request):
        try:
            assignment_date = datetime.datetime.strptime(request.query_params['date'], '%Y-%m-%d').date()
        except:
            assignment_date = datetime.date.today()
        
        response_couriers = []

        try:
            couriers = [Couriers.objects.get(pk=request.query_params['courier_id'])]
        except:
            couriers = Couriers.objects.all()
        
        for courier in couriers:

            courier_orders = [
                {
                    'order_id': order.pk,
                    'weight': order.weight,
                    'regions': order.regions,
                    'delivery_hours': order.delivery_hours,
                    'cost': order.cost
                } 
                for order in courier.orders.all().filter(assignment_date=assignment_date)
            ]

            if courier_orders:
                response_couriers.append(
                {'courier_id': courier.pk,
                'orders': {
                    'group_order_id': 1,
                    'orders': courier_orders
                    }}
                )
        
        assignment_date = datetime.datetime.strftime(assignment_date, '%Y-%m-%d')
        response_data = {
            'content': {
                'date': assignment_date,
                'couriers': sorted(response_couriers, key = lambda x: x['courier_id'])
            }
        }

        return Response(response_data, status=status.HTTP_200_OK) 


class OrdersViewSet(StoreViewSet):
    queryset = Orders.objects.all()
    serializer_class = OrdersSerializer
    pagination_class = OrdersPagination

    def create(self, request, *args, **kwargs):
        serializer = OrdersSerializer(data=request.data['content']['orders'], many=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        response_data = {
            'content': serializer.data
        }

        return Response(response_data, status=status.HTTP_200_OK)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({'content': serializer.data})

    @action(detail=False, methods=['POST'], url_path='complete')
    def complete_order(self, request):
        serializer = CompleteOrderSerializer(data=request.data['content']['complete_info'], 
                                             partial=True, many=True)

        if serializer.is_valid():
            data = serializer.validated_data
            response_data = []

            for order_dict in data:
                order = Orders.objects.get(pk=order_dict['order_id'])

                if order.courier.pk == order_dict['courier_id']:
                    order.complete_time = order_dict['complete_time']
                    order.save()

                    response_data.append({
                        'id':order.id,
                        'weight':order.weight,
                        'regions':order.regions,
                        'delivery_hours':order.delivery_hours,
                        'cost':order.cost,
                        'complete_time':order.complete_time
                    })

            return Response(response_data, status=status.HTTP_200_OK)

        return Response(status=status.HTTP_400_BAD_REQUEST)
    
    @staticmethod
    def overlap(working_hours, delivery_hours, limit):
        for delivery_interval in delivery_hours:
            for working_interval in working_hours:
                if working_interval[0] <= delivery_interval[0] <= delivery_interval[1] <= working_interval[1]:
                    return True
                elif working_interval[0] <= delivery_interval[0] <= working_interval[1] \
                    and (working_interval[1]-delivery_interval[0]).seconds / 60 >= limit:
                    return True
                elif delivery_interval[0] <= working_interval[0] <= delivery_interval[1] \
                    and (delivery_interval[1]-working_interval[0]).seconds / 60 >= limit:
                    return True
                elif delivery_interval[0] <= working_interval[1] <= delivery_interval[1] \
                    and (delivery_interval[1]-working_interval[1]).seconds / 60 >= limit:
                    return True
        return False
    
    @staticmethod
    def save_assigned_order(order, courier, assignment_date, coefficient, 
                            pending_assigned_orders, now_assigned_orders):
        order.courier = courier
        order.assignment_date = assignment_date
        order.cost = int(order.cost * coefficient)
        order.save()
        courier.orders.add(order)
        pending_assigned_orders.append(order)
        now_assigned_orders.append(
            {
                'order_id': order.pk,
                'weight': order.weight,
                'regions': order.regions,
                'delivery_hours': order.delivery_hours,
                'cost': order.cost
            } 
        )
        return now_assigned_orders

    def get_limit(self,  max_orders_amount, max_carriable_weight, max_regions_amount,
                            first_order_in_region_time, subsequent_orders_in_region_time,
                            order, courier, pending_assigned_orders):
        
        # Проверяет, может ли курьер взять ещё один заказ по лимиту 
        # на количество заказов, суммарный вес заказов и количество регионов для типа этого курьера
        if len(pending_assigned_orders) < max_orders_amount \
            and (sum([order.weight for order in pending_assigned_orders]) + order.weight) <= max_carriable_weight \
                and order.regions in courier.regions:
            
            pending_assigned_orders_regions = {o.regions for o in pending_assigned_orders}
            regions_amount = len(pending_assigned_orders_regions | {order.regions}) 
            if regions_amount <= max_regions_amount:
                
                # Считает количество суммарное времени, которое курьеру понадобится на выполнение 
                # имеющихся заказов плюс этого заказа
                if order.regions not in pending_assigned_orders_regions:
                    limit = regions_amount * first_order_in_region_time + (len(pending_assigned_orders) - regions_amount + 1) \
                        * subsequent_orders_in_region_time
                    coefficient = 1
                else:
                    limit = regions_amount * first_order_in_region_time + (len(pending_assigned_orders) - regions_amount) \
                        * subsequent_orders_in_region_time
                    coefficient = 0.8

                return limit, coefficient
        return False, None

    @action(detail=False, methods=['POST'], url_path='assign')
    def assign_orders(self, request):
        try:
            assignment_date = request.query_params.get['date']
        except:
            assignment_date = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d')

        orders = list(Orders.objects.filter(complete_time__isnull=True, courier__isnull=True))

        # Создаём из каждого из интервалов типа '10:00-11:00' список из двух datetime-объектов
        # пример: [datetime.datetime(2023, 5, 10, 10, 0), datetime.datetime(2023, 5, 10, 11, 0)]
        delivery_hours = [[
            [datetime.datetime.strptime(f'{assignment_date} {subinterval}', '%Y-%m-%d %H:%M') 
             for subinterval in interval.split('-')] 
             for interval in order.delivery_hours] 
             for order in orders
            ]
        
        # в delivery_hours[0] лежит orders[0].delivery_hours
        # => можно отсортировать список orders по списку delivery_hours
        # теперь в начале списка orders будут лежать заказы с самыми ранними значениями поля delivery_hours
        orders = sorted(orders, key=lambda order: delivery_hours[orders.index(order)])

        # повторно сортируем delivery_hours, чтобы delivery_hours[0] снова был равен orders[0].delivery_hours
        delivery_hours = sorted(delivery_hours)

        # возвращаем пеших курьеров, у которых меньше 2х недоставленных заказов
        couriers_foot = list(Couriers.objects.filter(
            courier_type='FOOT', 
            orders__complete_time__isnull=True
            ).annotate(num_pending_orders=Count('orders', filter=Q(orders__complete_time__isnull=True))
                       ).filter(num_pending_orders__lt=2))

        # возвращаем велокурьеров, у которых меньше 4х недоставленных заказов
        couries_bike = list(Couriers.objects.filter(
            courier_type='BIKE', 
            orders__complete_time__isnull=True
            ).annotate(num_pending_orders=Count('orders', filter=Q(orders__complete_time__isnull=True))
                       ).filter(num_pending_orders__lt=4))

        # возвращаем автокурьеров, у которых меньше 7 недоставленных заказов
        couriers_auto = list(Couriers.objects.filter(
            courier_type='AUTO', 
            orders__complete_time__isnull=True
            ).annotate(num_pending_orders=Count('orders', filter=Q(orders__complete_time__isnull=True))
                       ).filter(num_pending_orders__lt=7))
        
        couriers = couriers_foot + couries_bike + couriers_auto

        response_couriers = []

        for courier in couriers:
            pending_assigned_orders = list(courier.orders.filter(complete_time__isnull=True))
            now_assigned_orders = []
            working_hours = [
                [datetime.datetime.strptime(f'{assignment_date} {subinterval}', '%Y-%m-%d %H:%M') 
                    for subinterval in interval.split('-')] 
                for interval in courier.working_hours
            ]

            for order in orders:
                if order.courier == None: 

                    if courier.courier_type == 'FOOT':
                        limit, coefficient = self.get_limit(max_orders_amount=2, max_carriable_weight=10, max_regions_amount=1,
                            first_order_in_region_time=25, subsequent_orders_in_region_time=10,
                            order=order, courier=courier, pending_assigned_orders=pending_assigned_orders)
                        
                        if limit:
                            if self.overlap(working_hours, delivery_hours[orders.index(order)], limit):
                                self.save_assigned_order(order, courier, assignment_date, coefficient, 
                                                         pending_assigned_orders, now_assigned_orders)
                
                    elif courier.courier_type == 'BIKE':
                        limit, coefficient = self.get_limit(max_orders_amount=4, max_carriable_weight=20, max_regions_amount=2,
                            first_order_in_region_time=12, subsequent_orders_in_region_time=8,
                            order=order, courier=courier, pending_assigned_orders=pending_assigned_orders)
                        
                        if limit:
                            if self.overlap(working_hours, delivery_hours[orders.index(order)], limit):
                                self.save_assigned_order(order, courier, assignment_date, coefficient, 
                                                         pending_assigned_orders, now_assigned_orders)

                    elif courier.courier_type == 'AUTO':
                        limit, coefficient = self.get_limit(max_orders_amount=7, max_carriable_weight=40, max_regions_amount=4,
                            first_order_in_region_time=8, subsequent_orders_in_region_time=4,
                            order=order, courier=courier, pending_assigned_orders=pending_assigned_orders)
                        
                        if limit:
                            if self.overlap(working_hours, delivery_hours[orders.index(order)], limit):
                                self.save_assigned_order(order, courier, assignment_date, coefficient, 
                                                         pending_assigned_orders, now_assigned_orders)

            if now_assigned_orders:
                response_couriers.append(
                {'courier_id': courier.pk,
                'orders': {
                    'group_order_id': 1,
                    'orders': now_assigned_orders
                    }}
                )

        if type(assignment_date) == datetime.datetime:
            assignment_date = datetime.datetime.strftime(assignment_date, '%Y-%m-%d')

        response_data = {
            'content': {
                'date': assignment_date,
                'couriers': sorted(response_couriers, key = lambda x: x['courier_id'])
            }
        }

        return Response(response_data, status=status.HTTP_201_CREATED) 