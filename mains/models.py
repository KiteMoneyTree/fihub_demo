from django.db import models
from django.db.models import TextChoices

class Platform(models.Model):
    """
    Represents different e-commerce platforms (e.g., Flipkart, Amazon).
    """
    class Platforms(TextChoices):
        FLIPKART = 'FLIPKART', 'Flipkart'
        AMAZON = 'AMAZON', 'Amazon'
        MEESHO = 'MEESHO', 'Meesho' 
        # Add more platforms as needed

    platform_name = models.CharField(max_length=50, choices=Platforms.choices, unique=True)

    def __str__(self):
        return self.get_platform_name_display() 

class Customer(models.Model):
    """
    Represents a customer of the e-commerce platform.
    """
    customer_id = models.CharField(max_length=255, primary_key=True)
    customer_name = models.CharField(max_length=255)
    contact_email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.customer_name

class Order(models.Model):
    """
    Represents an order placed on the e-commerce platform.
    """
    order_id = models.CharField(max_length=255, primary_key=True)
    product_id = models.CharField(max_length=255)
    product_name = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    quantity_sold = models.IntegerField()
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    date_of_sale = models.DateField()
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    platform = models.ForeignKey(Platform, on_delete=models.CASCADE)
    coupon_used = models.BooleanField(default=False)
    return_window = models.IntegerField(null=True, blank=True)

    @property
    def total_sale_value(self):
        """
        Calculates the total sale value for the order.
        """
        return self.quantity_sold * self.selling_price

    def __str__(self):
        return f"Order ID: {self.order_id}"

class Delivery(models.Model):
    """
    Represents the delivery details of an order.
    """
    order = models.OneToOneField(Order, on_delete=models.CASCADE, primary_key=True)
    delivery_address = models.TextField()
    delivery_date = models.DateField()
    delivery_status = models.CharField(max_length=255)
    delivery_partner = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Delivery for Order ID: {self.order.order_id}"