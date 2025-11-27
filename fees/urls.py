from django.urls import path
from . import views

app_name = 'fees'

urlpatterns = [
    # Admin URLs
    path('admin/dashboard/', views.fee_management_dashboard, name='fee_management_dashboard'),
    path('admin/record-payment/', views.record_payment, name='record_payment'),
    path('admin/student/<int:student_id>/ledger/', views.student_ledger, name='student_ledger'),
    path('admin/arrears/', views.arrears_list, name='arrears_list'),
    path('admin/payment-history/', views.payment_history, name='payment_history'),

    # Student/Parent URLs
    path('student/dashboard/', views.student_fee_dashboard, name='student_fee_dashboard'),
    path('student/payment-history/', views.student_payment_history, name='student_payment_history'),
    path('student/download-receipt/<int:receipt_id>/', views.download_receipt, name='download_receipt'),
    path('student/request-payment-plan/', views.request_payment_plan, name='request_payment_plan'),

    # API URLs
    path('api/student/<int:student_id>/fee-info/', views.get_student_fee_info, name='student_fee_info'),
]