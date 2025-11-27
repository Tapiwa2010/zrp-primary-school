from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import models
from .forms import StudentRegistrationForm
from .models import User
from students.models import Student
from classes.models import Grade, ClassRoom, Teacher
from fees.models import FeeStructure, Payment

def landing(request):
    return render(request, 'landing.html')

def student_register(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            # Create user
            user = User.objects.create_user(
                username=form.cleaned_data['email'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                role='student'
            )
            # Create student profile
            Student.objects.create(
                user=user,
                grade=form.cleaned_data['grade'],
                class_room=form.cleaned_data.get('class_room')
            )
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('login')
    else:
        form = StudentRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        email = request.POST['username']  # username field is used for email
        password = request.POST['password']
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            if user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'teacher':
                return redirect('teacher_dashboard')
            elif user.role == 'student':
                return redirect('student_dashboard')
        else:
            messages.error(request, 'Invalid credentials')
    return render(request, 'accounts/login.html')

def admin_dashboard(request):
    if not request.user.is_authenticated or request.user.role != 'admin':
        return redirect('login')

    # Get statistics
    total_students = Student.objects.count()
    total_teachers = User.objects.filter(role='teacher').count()
    total_classes = ClassRoom.objects.count()
    total_grades = Grade.objects.count()

    # Get recent data
    recent_students = Student.objects.select_related('user', 'grade', 'class_room').order_by('-user__date_joined')[:5]
    teachers = User.objects.filter(role='teacher').order_by('first_name')
    grades = Grade.objects.all()
    classes = ClassRoom.objects.all()

    context = {
        'admin': request.user,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'total_grades': total_grades,
        'recent_students': recent_students,
        'teachers': teachers,
        'grades': grades,
        'classes': classes,
    }
    return render(request, 'admin/dashboard.html', context)

def teacher_dashboard(request):
    if not request.user.is_authenticated or request.user.role != 'teacher':
        return redirect('login')

    # Get teacher's assignments
    try:
        teacher_profile = Teacher.objects.get(user=request.user)
        assigned_classes = teacher_profile.assigned_classes.all()
        assigned_grades = teacher_profile.assigned_grades.all()

        # Get students in assigned classes or grades
        students = Student.objects.filter(
            models.Q(class_room__in=assigned_classes) | models.Q(grade__in=assigned_grades)
        ).select_related('user', 'grade', 'class_room').distinct()

    except Teacher.DoesNotExist:
        # If no teacher profile, show no students
        students = Student.objects.none()
        assigned_classes = ClassRoom.objects.none()
        assigned_grades = Grade.objects.none()

    # Get all grades and classes for reference
    grades = Grade.objects.all()
    classes = ClassRoom.objects.all()

    context = {
        'teacher': request.user,
        'students': students,
        'grades': grades,
        'classes': classes,
        'assigned_classes': assigned_classes,
        'assigned_grades': assigned_grades,
    }
    return render(request, 'teacher/dashboard.html', context)

def student_dashboard(request):
    if not request.user.is_authenticated or request.user.role != 'student':
        return redirect('login')
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        student = None
    return render(request, 'student/dashboard.html', {'student': student})

def student_academics(request):
    if not request.user.is_authenticated or request.user.role != 'student':
        return redirect('login')
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        student = None
    return render(request, 'student/academics.html', {'student': student})

def student_homework(request):
    if not request.user.is_authenticated or request.user.role != 'student':
        return redirect('login')
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        student = None
    return render(request, 'student/homework.html', {'student': student})

def student_attendance(request):
    if not request.user.is_authenticated or request.user.role != 'student':
        return redirect('login')
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        student = None
    return render(request, 'student/attendance.html', {'student': student})

def student_fees(request):
    if not request.user.is_authenticated or request.user.role != 'student':
        return redirect('login')
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        student = None
    return render(request, 'student/fees.html', {'student': student})

def student_communication(request):
    if not request.user.is_authenticated or request.user.role != 'student':
        return redirect('login')
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        student = None
    return render(request, 'student/communication.html', {'student': student})

def student_class_info(request):
    if not request.user.is_authenticated or request.user.role != 'student':
        return redirect('login')
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        student = None
    return render(request, 'student/class_info.html', {'student': student})

def student_profile(request):
    if not request.user.is_authenticated or request.user.role != 'student':
        return redirect('login')
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        student = None
    return render(request, 'student/profile.html', {'student': student})

def custom_logout(request):
    logout(request)
    return redirect('landing')

def admin_add_teacher(request):
    if not request.user.is_authenticated or request.user.role != 'admin':
        return redirect('login')

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            # Create teacher user
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role='teacher'
            )

            # Create teacher profile
            Teacher.objects.create(user=user)

            messages.success(request, f'Teacher {first_name} {last_name} created successfully!')
            return redirect('admin_dashboard')

        except Exception as e:
            messages.error(request, f'Error creating teacher: {str(e)}')

    return redirect('admin_dashboard')

def admin_manage_students(request):
    if not request.user.is_authenticated or request.user.role != 'admin':
        return redirect('login')

    students = Student.objects.all().select_related('user', 'grade', 'class_room')
    return render(request, 'admin/manage_students.html', {'students': students})

def admin_fee_management(request):
    if not request.user.is_authenticated or request.user.role != 'admin':
        return redirect('login')

    # Get fee structures
    fee_structures = FeeStructure.objects.all().select_related('grade')

    # Get recent payments
    recent_payments = Payment.objects.all().select_related('student__user', 'recorded_by').order_by('-payment_date')[:10]

    # Calculate totals
    total_expected = sum(fs.total_fee for fs in fee_structures)
    total_collected = Payment.objects.aggregate(total=models.Sum('amount'))['total'] or 0
    total_outstanding = total_expected - total_collected

    context = {
        'fee_structures': fee_structures,
        'recent_payments': recent_payments,
        'total_expected': total_expected,
        'total_collected': total_collected,
        'total_outstanding': total_outstanding,
    }
    return render(request, 'admin/fee_management.html', context)

def admin_record_payment(request):
    if not request.user.is_authenticated or request.user.role != 'admin':
        return redirect('login')

    # Redirect to the new fee management system
    return redirect('record_payment')

def teacher_add_student(request):
    if not request.user.is_authenticated or request.user.role != 'teacher':
        return redirect('login')

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        grade_id = request.POST.get('grade')
        class_room_id = request.POST.get('class_room')

        try:
            grade = Grade.objects.get(id=grade_id)
            class_room = None
            if class_room_id:
                class_room = ClassRoom.objects.get(id=class_room_id)

            # Check if teacher is assigned to this grade/class
            teacher_profile = Teacher.objects.get(user=request.user)
            if grade not in teacher_profile.assigned_grades.all() and (class_room and class_room not in teacher_profile.assigned_classes.all()):
                messages.error(request, 'You are not authorized to add students to this grade/class.')
                return redirect('teacher_dashboard')

            # Create user
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role='student'
            )

            # Create student profile
            Student.objects.create(
                user=user,
                grade=grade,
                class_room=class_room
            )

            messages.success(request, f'Student {first_name} {last_name} registered successfully!')
            return redirect('teacher_dashboard')

        except Grade.DoesNotExist:
            messages.error(request, 'Invalid grade selected.')
        except ClassRoom.DoesNotExist:
            messages.error(request, 'Invalid class selected.')
        except Exception as e:
            messages.error(request, f'Error registering student: {str(e)}')

    return redirect('teacher_dashboard')
