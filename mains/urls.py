from django.urls import include, re_path
from mains import views 
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    re_path('api/monthly_sales/', views.MonthlySalesVolume.as_view(), name='monthly_sales'),
    re_path('api/monthly_revenue/', views.MonthlyRevenue.as_view(), name='monthly_revenue'),
    re_path('api/summary_metrics/', views.summary_metrics, name='summary_metrics'),
    re_path('api/download_csv/', views.download_filtered_csv, name='download_filtered_csv'),
    re_path('api/categories/', views.CategoryList.as_view(), name='category_list'),
    re_path('dashboard/', views.dashboard, name='dashboard'),  # Define a URL for the dashboard
]