from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.template.loader import get_template
from django.core.paginator import Paginator
from decimal import Decimal
import json

from .models import (
    FeeStructure, StudentLedger, Payment, Receipt, FeeReminder,
    AcademicYear, Term, PaymentMethod, Discount, PaymentPlan,
    Refund, AuditLog, AgentPayment
)
from students.models import Student
from accounts.models import User

# Admin Views

@login_required
def fee_management_dashboard(request):
    """Main fee management dashboard for admins"""
    if not request.user.is_staff:
        return redirect('student_fee_dashboard')

    # Get current academic year and term
    current_year = AcademicYear.objects.filter(is_current=True).first()
    current_term = Term.objects.filter(is_current=True).first()

    # Financial overview
    total_expected = StudentLedger.objects.filter(
        academic_year=current_year,
        term=current_term
    ).aggregate(total=Sum('total_required'))['total'] or 0

    total_collected = Payment.objects.filter(
        ledger__academic_year=current_year,
        ledger__term=current_term,
        status='verified'
    ).aggregate(total=Sum('amount'))['total'] or 0

    total_outstanding = total_expected - total_collected

    # Calculate collection rate
    collection_rate = 0
    if total_expected > 0:
        collection_rate = (total_collected / total_expected) * 100

    # Today's collections
    today = timezone.now().date()
    todays_collections = Payment.objects.filter(
        payment_date__date=today,
        status='verified'
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Student payment status
    total_students = Student.objects.count()
    fully_paid_students = StudentLedger.objects.filter(
        academic_year=current_year,
        term=current_term,
        outstanding_balance__lte=0
    ).count()

    # Recent payments
    recent_payments = Payment.objects.select_related(
        'student__user', 'recorded_by', 'payment_method'
    ).order_by('-payment_date')[:10]

    # Fee structures
    fee_structures = FeeStructure.objects.select_related(
        'academic_year', 'term', 'grade'
    ).filter(academic_year=current_year).order_by('grade__name')

    context = {
        'total_expected': total_expected,
        'total_collected': total_collected,
        'total_outstanding': total_outstanding,
        'collection_rate': collection_rate,
        'todays_collections': todays_collections,
        'total_students': total_students,
        'fully_paid_students': fully_paid_students,
        'recent_payments': recent_payments,
        'fee_structures': fee_structures,
        'current_year': current_year,
        'current_term': current_term,
    }

    return render(request, 'admin/fee_management.html', context)

@login_required
def record_payment(request):
    """Record a new payment"""
    if not request.user.is_staff:
        return redirect('student_fee_dashboard')

    if request.method == 'POST':
        student_id = request.POST.get('student')
        amount = Decimal(request.POST.get('amount'))
        payment_method_id = request.POST.get('payment_method')
        reference = request.POST.get('reference', '')
        notes = request.POST.get('notes', '')

        try:
            student = Student.objects.get(id=student_id)
            payment_method = PaymentMethod.objects.get(id=payment_method_id)

            # Get or create current ledger
            current_year = AcademicYear.objects.filter(is_current=True).first()
            current_term = Term.objects.filter(is_current=True).first()

            ledger, created = StudentLedger.objects.get_or_create(
                student=student,
                academic_year=current_year,
                term=current_term,
                defaults={'term_fees': 0, 'payments_made': 0}
            )

            # Create payment
            payment = Payment.objects.create(
                student=student,
                ledger=ledger,
                amount=amount,
                payment_method=payment_method,
                reference_number=reference,
                recorded_by=request.user,
                notes=notes,
                status='verified'  # Auto-verify for admin recorded payments
            )

            # Update ledger
            ledger.payments_made += amount
            ledger.last_payment_date = timezone.now()
            ledger.update_balances()

            # Create receipt
            Receipt.objects.create(
                payment=payment,
                amount_paid=amount,
                previous_balance=ledger.outstanding_balance + amount,
                new_balance=ledger.outstanding_balance,
                generated_by=request.user
            )

            # Log audit
            AuditLog.objects.create(
                user=request.user,
                action_type='payment_recorded',
                description=f"Payment of ${amount} recorded for {student}",
                student=student,
                amount=amount
            )

            messages.success(request, f'Payment recorded successfully. Receipt: {payment.receipt.receipt_number}')
            return redirect('fee_management_dashboard')

        except Exception as e:
            messages.error(request, f'Error recording payment: {str(e)}')

    # GET request - show form
    students = Student.objects.select_related('user', 'grade').order_by('user__first_name')
    payment_methods = PaymentMethod.objects.filter(is_active=True)

    context = {
        'students': students,
        'payment_methods': payment_methods,
    }

    return render(request, 'admin/record_payment.html', context)

@login_required
def student_ledger(request, student_id):
    """View detailed student ledger"""
    if not request.user.is_staff:
        return redirect('student_fee_dashboard')

    student = get_object_or_404(Student, id=student_id)

    # Get current ledger
    current_year = AcademicYear.objects.filter(is_current=True).first()
    current_term = Term.objects.filter(is_current=True).first()

    ledger = StudentLedger.objects.filter(
        student=student,
        academic_year=current_year,
        term=current_term
    ).first()

    # Payment history
    payments = Payment.objects.filter(
        student=student
    ).select_related('payment_method', 'recorded_by').order_by('-payment_date')

    context = {
        'student': student,
        'ledger': ledger,
        'payments': payments,
        'current_year': current_year,
        'current_term': current_term,
    }

    return render(request, 'admin/student_ledger.html', context)

@login_required
def arrears_list(request):
    """List of students with outstanding fees"""
    if not request.user.is_staff:
        return redirect('student_fee_dashboard')

    current_year = AcademicYear.objects.filter(is_current=True).first()
    current_term = Term.objects.filter(is_current=True).first()

    # Filter parameters
    grade_filter = request.GET.get('grade')
    min_amount = request.GET.get('min_amount', 0)

    ledgers = StudentLedger.objects.filter(
        academic_year=current_year,
        term=current_term,
        outstanding_balance__gt=min_amount
    ).select_related('student__user', 'student__grade')

    if grade_filter:
        ledgers = ledgers.filter(student__grade_id=grade_filter)

    # Pagination
    paginator = Paginator(ledgers, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'current_year': current_year,
        'current_term': current_term,
    }

    return render(request, 'admin/arrears_list.html', context)

@login_required
def payment_history(request):
    """Complete payment history"""
    if not request.user.is_staff:
        return redirect('student_fee_dashboard')

    # Filters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    payment_method = request.GET.get('payment_method')
    recorded_by = request.GET.get('recorded_by')

    payments = Payment.objects.select_related(
        'student__user', 'payment_method', 'recorded_by'
    ).order_by('-payment_date')

    if start_date:
        payments = payments.filter(payment_date__date__gte=start_date)
    if end_date:
        payments = payments.filter(payment_date__date__lte=end_date)
    if payment_method:
        payments = payments.filter(payment_method_id=payment_method)
    if recorded_by:
        payments = payments.filter(recorded_by_id=recorded_by)

    # Pagination
    paginator = Paginator(payments, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Summary stats
    total_amount = payments.aggregate(total=Sum('amount'))['total'] or 0
    payment_count = payments.count()

    context = {
        'page_obj': page_obj,
        'total_amount': total_amount,
        'payment_count': payment_count,
        'payment_methods': PaymentMethod.objects.filter(is_active=True),
        'staff_users': User.objects.filter(is_staff=True),
    }

    return render(request, 'admin/payment_history.html', context)

# Student/Parent Views

@login_required
def student_fee_dashboard(request):
    """Student fee dashboard"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('dashboard')

    # Get current ledger
    current_year = AcademicYear.objects.filter(is_current=True).first()
    current_term = Term.objects.filter(is_current=True).first()

    ledger = StudentLedger.objects.filter(
        student=student,
        academic_year=current_year,
        term=current_term
    ).first()

    # Fee breakdown
    fee_structure = FeeStructure.objects.filter(
        academic_year=current_year,
        term=current_term,
        grade=student.grade,
        is_boarder=False  # Assuming day scholar for now
    ).first()

    # Recent payments
    recent_payments = Payment.objects.filter(
        student=student
    ).select_related('payment_method').order_by('-payment_date')[:5]

    # Payment plan if exists
    payment_plan = PaymentPlan.objects.filter(
        student=student,
        status='active'
    ).first()

    context = {
        'student': student,
        'ledger': ledger,
        'fee_structure': fee_structure,
        'recent_payments': recent_payments,
        'payment_plan': payment_plan,
        'current_year': current_year,
        'current_term': current_term,
    }

    return render(request, 'student/fees.html', context)

@login_required
def student_payment_history(request):
    """Student payment history"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('dashboard')

    payments = Payment.objects.filter(
        student=student
    ).select_related('payment_method', 'receipt').order_by('-payment_date')

    context = {
        'student': student,
        'payments': payments,
    }

    return render(request, 'student/payment_history.html', context)

@login_required
def download_receipt(request, receipt_id):
    """Download payment receipt"""
    try:
        student = Student.objects.get(user=request.user)
        receipt = get_object_or_404(Receipt, id=receipt_id, payment__student=student)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('dashboard')

    # In a real implementation, you'd generate a PDF here
    # For now, just return the receipt data as JSON
    data = {
        'receipt_number': receipt.receipt_number,
        'student': str(receipt.payment.student),
        'amount': str(receipt.amount_paid),
        'date': receipt.generated_at.strftime('%Y-%m-%d'),
        'method': receipt.payment.payment_method.name,
    }

    return JsonResponse(data)

@login_required
def request_payment_plan(request):
    """Request a payment plan"""
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('dashboard')

    if request.method == 'POST':
        total_amount = Decimal(request.POST.get('total_amount'))
        installments = int(request.POST.get('installments'))

        # Create payment plan request
        PaymentPlan.objects.create(
            student=student,
            total_amount=total_amount,
            number_of_installments=installments,
            installment_amount=total_amount / installments,
            start_date=timezone.now().date(),
            status='pending',  # Would need admin approval
            created_by=request.user
        )

        messages.success(request, 'Payment plan request submitted. Awaiting approval.')
        return redirect('student_fee_dashboard')

    return render(request, 'student/request_payment_plan.html')

# API Views for AJAX

def get_student_fee_info(request, student_id):
    """API endpoint to get student fee information"""
    if not request.user.is_staff:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    student = get_object_or_404(Student, id=student_id)
    current_year = AcademicYear.objects.filter(is_current=True).first()
    current_term = Term.objects.filter(is_current=True).first()

    ledger = StudentLedger.objects.filter(
        student=student,
        academic_year=current_year,
        term=current_term
    ).first()

    data = {
        'student_name': str(student),
        'admission_number': student.user.username,  # Assuming username is admission number
        'class': str(student.grade),
        'total_required': str(ledger.total_required) if ledger else '0',
        'paid_amount': str(ledger.payments_made) if ledger else '0',
        'outstanding': str(ledger.outstanding_balance) if ledger else '0',
    }

    return JsonResponse(data)
