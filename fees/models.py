from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal

class AcademicYear(models.Model):
    """Academic year for fee structures"""
    name = models.CharField(max_length=20, unique=True)  # e.g., "2025"
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Term(models.Model):
    """School terms"""
    TERM_CHOICES = [
        ('term1', 'Term 1'),
        ('term2', 'Term 2'),
        ('term3', 'Term 3'),
    ]
    name = models.CharField(max_length=10, choices=TERM_CHOICES, unique=True)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} - {self.academic_year.name}"

class FeeComponent(models.Model):
    """Individual fee components"""
    COMPONENT_TYPES = [
        ('tuition', 'Tuition Fee'),
        ('exam', 'Examination Fee'),
        ('development', 'Development Levy'),
        ('building', 'Building Fund'),
        ('sports', 'Sports Levy'),
        ('library', 'Library Fee'),
        ('laboratory', 'Laboratory Fee'),
        ('computer', 'Computer Lab Fee'),
        ('transport', 'Transport Fee'),
        ('boarding', 'Boarding Fee'),
        ('extra_classes', 'Extra Classes Fee'),
        ('activity', 'Activity Fee'),
    ]

    name = models.CharField(max_length=50, choices=COMPONENT_TYPES, unique=True)
    description = models.TextField(blank=True)
    is_mandatory = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.get_name_display()

class FeeStructure(models.Model):
    """Comprehensive fee structure per grade and term"""
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, null=True, blank=True)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True, blank=True)
    grade = models.ForeignKey('classes.Grade', on_delete=models.CASCADE)
    currency = models.CharField(max_length=3, default='USD', choices=[('USD', 'USD'), ('ZWL', 'ZWL'), ('ZAR', 'ZAR')])

    # Fee components
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    exam_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    development_levy = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    building_fund = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sports_levy = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    library_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    laboratory_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    computer_lab_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transport_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    boarding_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    extra_classes_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    activity_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    total_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_deadline = models.DateField(null=True, blank=True)
    early_payment_discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # percentage
    late_payment_penalty = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # percentage

    # For different student types
    is_day_scholar = models.BooleanField(default=True)
    is_boarder = models.BooleanField(default=False)


    class Meta:
        unique_together = ['academic_year', 'term', 'grade', 'is_day_scholar']

    def save(self, *args, **kwargs):
        self.total_fee = (
            self.tuition_fee + self.exam_fee + self.development_levy +
            self.building_fund + self.sports_levy + self.library_fee +
            self.laboratory_fee + self.computer_lab_fee + self.transport_fee +
            self.boarding_fee + self.extra_classes_fee + self.activity_fee
        )
        super().save(*args, **kwargs)

    def __str__(self):
        student_type = "Boarder" if self.is_boarder else "Day Scholar"
        return f"{self.grade.name} - {self.term.name} {self.academic_year.name} ({student_type}) - {self.currency} {self.total_fee}"

class StudentLedger(models.Model):
    """Complete financial record for each student"""
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, null=True, blank=True)
    term = models.ForeignKey(Term, on_delete=models.CASCADE, null=True, blank=True)

    # Balances
    opening_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Arrears from previous term
    term_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_required = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payments_made = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    outstanding_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Status tracking
    last_payment_date = models.DateTimeField(null=True, blank=True)
    flagged_for_followup = models.BooleanField(default=False)
    notes = models.TextField(blank=True)


    class Meta:
        unique_together = ['student', 'academic_year', 'term']

    def update_balances(self):
        self.total_required = self.opening_balance + self.term_fees
        self.outstanding_balance = self.total_required - self.payments_made
        self.save()

    def __str__(self):
        return f"{self.student} - {self.term.name} {self.academic_year.name}"

class PaymentMethod(models.Model):
    """Available payment methods"""
    METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('ecocash', 'Ecocash'),
        ('bank_transfer', 'Bank Transfer'),
        ('zipit', 'ZIPIT'),
        ('swipe', 'Swipe (POS)'),
        ('cheque', 'Cheque'),
        ('paynow', 'Paynow'),
        ('innbucks', 'InnBucks'),
    ]

    name = models.CharField(max_length=20, choices=METHOD_CHOICES, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    requires_reference = models.BooleanField(default=False)

    def __str__(self):
        return self.get_name_display()

class Payment(models.Model):
    """Student fee payments with enhanced tracking"""
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    ledger = models.ForeignKey(StudentLedger, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE)
    reference_number = models.CharField(max_length=100, blank=True)
    payment_date = models.DateTimeField(default=timezone.now)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    # Additional info
    notes = models.TextField(blank=True)
    upload_proof = models.FileField(upload_to='payment_proofs/', blank=True, null=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='verified_payments', null=True, blank=True)


    def __str__(self):
        return f"{self.student} - {self.amount} - {self.payment_method} - {self.status}"

class Receipt(models.Model):
    """Payment receipts"""
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE)
    receipt_number = models.CharField(max_length=50, unique=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # Receipt details
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    previous_balance = models.DecimalField(max_digits=10, decimal_places=2)
    new_balance = models.DecimalField(max_digits=10, decimal_places=2)

    # PDF storage
    pdf_file = models.FileField(upload_to='receipts/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            # Generate receipt number: RCP-YYYY-NNNNNN
            year = timezone.now().year
            last_receipt = Receipt.objects.filter(receipt_number__startswith=f'RCP-{year}').order_by('-receipt_number').first()
            if last_receipt:
                last_num = int(last_receipt.receipt_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            self.receipt_number = f'RCP-{year}-{new_num:06d}'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.receipt_number

class FeeReminder(models.Model):
    """Automated reminders for fee payments"""
    REMINDER_TYPES = [
        ('payment_due', 'Payment Due'),
        ('overdue', 'Overdue Payment'),
        ('final_notice', 'Final Notice'),
        ('receipt_confirmation', 'Receipt Confirmation'),
    ]

    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPES)
    message = models.TextField()
    sent_via_sms = models.BooleanField(default=False)
    sent_via_email = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.student} - {self.reminder_type} - {self.sent_at.date()}"

class Discount(models.Model):
    """Fee discounts and scholarships"""
    DISCOUNT_TYPES = [
        ('sibling', 'Sibling Discount'),
        ('early_payment', 'Early Payment Discount'),
        ('full_scholarship', 'Full Scholarship'),
        ('partial_scholarship', 'Partial Scholarship'),
        ('staff_child', 'Staff Child Discount'),
        ('hardship', 'Hardship Case'),
    ]

    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # 0-100
    fixed_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reason = models.TextField()
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    approved_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.student} - {self.discount_type} - {self.percentage}%"

class PaymentPlan(models.Model):
    """Installment payment plans"""
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    ledger = models.ForeignKey(StudentLedger, on_delete=models.CASCADE, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    number_of_installments = models.PositiveIntegerField()
    installment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('defaulted', 'Defaulted'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.number_of_installments} installments - {self.status}"

class Refund(models.Model):
    """Fee refunds and credits"""
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField()
    refund_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE)

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('processed', 'Processed'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='requested_refunds')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='approved_refunds')
    processed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - Refund ${self.amount} - {self.status}"

class AuditLog(models.Model):
    """Audit trail for all fee-related actions"""
    ACTION_TYPES = [
        ('payment_recorded', 'Payment Recorded'),
        ('payment_verified', 'Payment Verified'),
        ('receipt_generated', 'Receipt Generated'),
        ('discount_applied', 'Discount Applied'),
        ('refund_processed', 'Refund Processed'),
        ('ledger_edited', 'Ledger Edited'),
        ('fee_structure_changed', 'Fee Structure Changed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    action_type = models.CharField(max_length=25, choices=ACTION_TYPES)
    description = models.TextField()
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action_type} - {self.timestamp}"

class ExchangeRate(models.Model):
    """Currency exchange rates"""
    from_currency = models.CharField(max_length=3)
    to_currency = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=10, decimal_places=4)
    date = models.DateField(default=timezone.now)

    class Meta:
        unique_together = ['from_currency', 'to_currency', 'date']

    def __str__(self):
        return f"1 {self.from_currency} = {self.rate} {self.to_currency} ({self.date})"

class BankReconciliation(models.Model):
    """Bank reconciliation records"""
    date = models.DateField()
    bank_balance = models.DecimalField(max_digits=10, decimal_places=2)
    book_balance = models.DecimalField(max_digits=10, decimal_places=2)
    difference = models.DecimalField(max_digits=10, decimal_places=2)
    reconciled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bank Reconciliation - {self.date}"

class AgentPayment(models.Model):
    """Mobile money agent payments"""
    agent_name = models.CharField(max_length=100)
    agent_phone = models.CharField(max_length=20)
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    reference = models.CharField(max_length=100)
    collected_at = models.DateTimeField()
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('paid', 'Paid to Agent'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.0)  # percentage
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.commission_amount = (self.amount * self.commission_rate) / 100
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.agent_name} - {self.student} - ${self.amount}"
