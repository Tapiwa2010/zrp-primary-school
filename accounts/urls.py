from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.student_register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('teacher-dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('admin/add-teacher/', views.admin_add_teacher, name='admin_add_teacher'),
    path('admin/manage-students/', views.admin_manage_students, name='admin_manage_students'),
    path('admin/fee-management/', views.admin_fee_management, name='admin_fee_management'),
    path('admin/record-payment/', views.admin_record_payment, name='admin_record_payment'),
    path('teacher/add-student/', views.teacher_add_student, name='teacher_add_student'),
    path('student/academics/', views.student_academics, name='student_academics'),
    path('student/homework/', views.student_homework, name='student_homework'),
    path('student/attendance/', views.student_attendance, name='student_attendance'),
    path('student/fees/', views.student_fees, name='student_fees'),
    path('student/communication/', views.student_communication, name='student_communication'),
    path('student/class-info/', views.student_class_info, name='student_class_info'),
    path('student/profile/', views.student_profile, name='student_profile'),
]