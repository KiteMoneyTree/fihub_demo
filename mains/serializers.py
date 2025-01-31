from rest_framework import serializers
from .models import Platform, Customer, Order, Delivery

class MonthlySalesVolumeSerializer(serializers.Serializer):  # Note: serializers.Serializer
    month = serializers.DateField()  # For the date field
    total_quantity = serializers.IntegerField()  # For the aggregated quantity

class MonthlyRevenueSerializer(serializers.Serializer):  # Note: serializers.Serializer
    month = serializers.DateField()  # For the date field
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2) # For the aggregated revenue

class CategorySerializer(serializers.Serializer):
    category = serializers.SerializerMethodField()

    def get_category(self, obj):
        return obj  # obj will be the string (category name) itself
