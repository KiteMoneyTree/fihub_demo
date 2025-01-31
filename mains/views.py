import csv
from rest_framework import generics, views, response, status
from rest_framework.decorators import api_view
from django.db.models import Sum, Count, Case, When, IntegerField, FloatField, F, DecimalField
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from mains.models import Order
from mains.serializers import MonthlyRevenueSerializer, MonthlySalesVolumeSerializer, CategorySerializer
from django.shortcuts import render

def dashboard(request):
    return render(request, 'dashboard.html')  # 'dashboard.html' is relative to the 'templates' directory

class CategoryList(generics.ListAPIView):
    queryset = Order.objects.values_list('category', flat=True).distinct()
    serializer_class = CategorySerializer

class MonthlySalesVolume(generics.ListAPIView):
    """
    API endpoint to retrieve monthly sales volume (quantity sold).

    Supports filtering by date range, product category, delivery status, and platform.
    """
    serializer_class = MonthlySalesVolumeSerializer  # Use the serializer for monthly sales data

    def get_queryset(self):
        """
        Returns a queryset of aggregated monthly sales volume, filtered by request parameters.
        """
        queryset = Order.objects.all()  # Start with all orders

        # Get filter parameters from the request
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        category = self.request.GET.get('category')
        delivery_status = self.request.GET.get('delivery_status')
        platform = self.request.GET.get('platform')

        # Apply filters if parameters are provided
        if start_date:
            queryset = queryset.filter(date_of_sale__gte=start_date)  # Filter by start date
        if end_date:
            queryset = queryset.filter(date_of_sale__lte=end_date)  # Filter by end date
        if category:
            queryset = queryset.filter(category=category)  # Filter by product category
        if delivery_status:
            queryset = queryset.filter(delivery__delivery_status=delivery_status)  # Filter by delivery status
        if platform:
            queryset = queryset.filter(platform__platform_name=platform)  # Filter by platform

        # Aggregate data by month and calculate total quantity sold
        queryset = queryset.annotate(
            month=TruncMonth('date_of_sale')  # Truncate date to the beginning of the month
        ).values('month').annotate(
            total_quantity=Sum('quantity_sold')  # Sum the quantity sold for each month
        ).order_by('month')  # Order the results by month

        return queryset  # Return the filtered and aggregated queryset


class MonthlyRevenue(generics.ListAPIView):
    """
    API endpoint to retrieve monthly revenue (total sale value).

    Supports filtering by date range, product category, delivery status, and platform.
    """
    serializer_class = MonthlyRevenueSerializer  # Use the serializer for monthly revenue data

    def get_queryset(self):
        """
        Returns a queryset of aggregated monthly revenue, filtered by request parameters.
        """
        queryset = Order.objects.all()  # Start with all orders

        # Get filter parameters from the request
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        category = self.request.GET.get('category')
        delivery_status = self.request.GET.get('delivery_status')
        platform = self.request.GET.get('platform')

        # Apply filters if parameters are provided
        if start_date:
            queryset = queryset.filter(date_of_sale__gte=start_date)  # Filter by start date
        if end_date:
            queryset = queryset.filter(date_of_sale__lte=end_date)  # Filter by end date
        if category:
            queryset = queryset.filter(category=category)  # Filter by product category
        if delivery_status:
            queryset = queryset.filter(delivery__delivery_status=delivery_status)  # Filter by delivery status
        if platform:
            queryset = queryset.filter(platform__platform_name=platform)  # Filter by platform

        # Calculate total sale value and aggregate data by month
        queryset = queryset.annotate(
            total_sale_value=F('quantity_sold') * F('selling_price'),  # Calculate total sale value for each order
            month=TruncMonth('date_of_sale')  # Truncate date to the beginning of the month
        ).values('month').annotate(
            total_quantity=Sum('quantity_sold'), # Sum of quantities sold per month (optional, if needed)
            total_revenue=Sum('total_sale_value', output_field=DecimalField())  # Sum the total sale value for each month. output_field is important for decimal places

        ).order_by('month')  # Order the results by month

        return queryset  # Return the filtered and aggregated queryset


@api_view(['GET'])
def summary_metrics(request):
    """
    API endpoint to retrieve summary metrics: total revenue, total orders, 
    total products sold, and canceled order percentage.

    Supports filtering by date range, product category, delivery status, and platform.
    """

    # Get filter parameters from the request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    category = request.GET.get('category')
    delivery_status = request.GET.get('delivery_status')
    platform = request.GET.get('platform')

    # Start with all orders and apply filters if provided
    queryset = Order.objects.all()
    if start_date:
        queryset = queryset.filter(date_of_sale__gte=start_date)  # Filter by start date
    if end_date:
        queryset = queryset.filter(date_of_sale__lte=end_date)  # Filter by end date
    if category:
        queryset = queryset.filter(category=category)  # Filter by product category
    if delivery_status:
        queryset = queryset.filter(delivery__delivery_status=delivery_status)  # Filter by delivery status
    if platform:
        queryset = queryset.filter(platform__platform_name=platform)  # Filter by platform

    # Calculate total_sale_value for each order *before* aggregation
    queryset = queryset.annotate(
        total_sale_value=F('quantity_sold') * F('selling_price'),  # Calculate total sale value
    )

    # Aggregate metrics
    total_revenue = queryset.aggregate(total_revenue=Sum('total_sale_value', output_field=DecimalField()))['total_revenue'] or 0  # Sum of total sale values
    total_orders = queryset.count()  # Total number of orders
    total_products_sold = queryset.aggregate(total_products_sold=Sum('quantity_sold'))['total_products_sold'] or 0  # Sum of quantities sold

    # Calculate canceled order percentage
    total_cancelled_orders = queryset.filter(delivery__delivery_status='Cancelled').count()  # Number of cancelled orders
    canceled_order_percentage = (total_cancelled_orders / total_orders) * 100 if total_orders else 0  # Percentage of cancelled orders

    # Prepare the response data
    data = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'total_products_sold': total_products_sold,
        'canceled_order_percentage': canceled_order_percentage,
    }
    return response.Response(data)  # Return the summary metrics data

@api_view(['GET'])
def download_filtered_csv(request):
    """
    Downloads a CSV file of orders, filtered by query parameters.

    Supports filtering by date range, product category, delivery status, and platform.
    """

    # Get filter parameters from the request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    category = request.GET.get('category')
    delivery_status = request.GET.get('delivery_status')
    platform = request.GET.get('platform')

    # Start with all orders and apply filters if provided
    queryset = Order.objects.all()

    if start_date:
        queryset = queryset.filter(date_of_sale__gte=start_date)  # Filter by start date
    if end_date:
        queryset = queryset.filter(date_of_sale__lte=end_date)  # Filter by end date
    if category:
        queryset = queryset.filter(category=category)  # Filter by product category
    if delivery_status:
        queryset = queryset.filter(delivery__delivery_status=delivery_status)  # Filter by delivery status (assuming 'delivery' is a related field)
    if platform:
        queryset = queryset.filter(platform__platform_name=platform)  # Filter by platform (assuming 'platform' is a related field)

    # Prepare the CSV response
    response = HttpResponse(content_type='text/csv')  # Set the content type for CSV
    response['Content-Disposition'] = 'attachment; filename="filtered_orders.csv"'  # Set the filename for download

    writer = csv.writer(response)  # Create a CSV writer object

    # Write the header row (field names) dynamically
    field_names = [field.name for field in Order._meta.get_fields() if not field.many_to_one]  # Get all field names from the Order model (excluding foreign keys)
    writer.writerow(field_names)  # Write the field names as the header row

    # Write the data rows
    for obj in queryset:  # Iterate through the filtered queryset
        row_data = [getattr(obj, field) for field in field_names]  # Get the value of each field for the current object
        writer.writerow(row_data)  # Write the data row to the CSV

    return response  # Return the CSV response