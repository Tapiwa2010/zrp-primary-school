from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    AcademicYear, Term, FeeComponent, FeeStructure, StudentLedger,
    PaymentMethod, Payment, Receipt, FeeReminder, Discount,
    PaymentPlan, Refund, AuditLog, ExchangeRate, BankReconciliation, AgentPayment
)

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_current')
    list_editable = ('is_current',)

@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year', 'start_date', 'end_date', 'is_current')
    list_filter = ('academic_year', 'is_current')
    list_editable = ('is_current',)

@admin.register(FeeComponent)
class FeeComponentAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_mandatory', 'is_active')
    list_editable = ('is_mandatory', 'is_active')

@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ('grade', 'term', 'academic_year', 'total_fee', 'currency', 'is_boarder', 'payment_deadline')
    list_filter = ('academic_year', 'term', 'grade', 'is_boarder', 'currency')
    search_fields = ('grade__name',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('academic_year', 'term', 'grade', 'currency', 'is_day_scholar', 'is_boarder')
        }),
        ('Fee Components', {
            'fields': (
                'tuition_fee', 'exam_fee', 'development_levy', 'building_fund',
                'sports_levy', 'library_fee', 'laboratory_fee', 'computer_lab_fee',
                'transport_fee', 'boarding_fee', 'extra_classes_fee', 'activity_fee'
            )
        }),
        ('Settings', {
            'fields': ('payment_deadline', 'early_payment_discount', 'late_payment_penalty')
        }),
    )
    readonly_fields = ('total_fee',)

@admin.register(StudentLedger)
class StudentLedgerAdmin(admin.ModelAdmin):
    list_display = ('student', 'term', 'academic_year', 'total_required', 'payments_made', 'outstanding_balance', 'flagged_for_followup')
    list_filter = ('academic_year', 'term', 'flagged_for_followup')
    search_fields = ('student__user__first_name', 'student__user__last_name')
    readonly_fields = ('outstanding_balance',)
    actions = ['flag_for_followup', 'unflag_for_followup']

    def flag_for_followup(self, request, queryset):
        queryset.update(flagged_for_followup=True)
    flag_for_followup.short_description = "Flag selected ledgers for follow-up"

    def unflag_for_followup(self, request, queryset):
        queryset.update(flagged_for_followup=False)
    unflag_for_followup.short_description = "Remove follow-up flag from selected ledgers"

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'requires_reference')
    list_editable = ('is_active', 'requires_reference')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount', 'payment_method', 'status', 'payment_date', 'recorded_by', 'receipt_link')
    list_filter = ('status', 'payment_method', 'payment_date', 'recorded_by')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'reference_number')
    readonly_fields = ('verified_at',)
    actions = ['verify_payments', 'reject_payments']

    def receipt_link(self, obj):
        if hasattr(obj, 'receipt'):
            return format_html('<a href="{}" target="_blank">View Receipt</a>', reverse('admin:fees_receipt_change', args=(obj.receipt.id,)))
        return "No Receipt"
    receipt_link.short_description = "Receipt"

    def verify_payments(self, request, queryset):
        queryset.update(status='verified', verified_at=timezone.now(), verified_by=request.user)
    verify_payments.short_description = "Verify selected payments"

    def reject_payments(self, request, queryset):
        queryset.update(status='failed')
    reject_payments.short_description = "Reject selected payments"

@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'payment', 'amount_paid', 'generated_at', 'generated_by')
    search_fields = ('receipt_number', 'payment__student__user__first_name', 'payment__student__user__last_name')
    readonly_fields = ('receipt_number',)

@admin.register(FeeReminder)
class FeeReminderAdmin(admin.ModelAdmin):
    list_display = ('student', 'reminder_type', 'sent_via_sms', 'sent_via_email', 'sent_at', 'sent_by')
    list_filter = ('reminder_type', 'sent_at', 'sent_by')
    search_fields = ('student__user__first_name', 'student__user__last_name')

@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('student', 'discount_type', 'percentage', 'fixed_amount', 'is_active', 'approved_by')
    list_filter = ('discount_type', 'is_active', 'approved_by')
    search_fields = ('student__user__first_name', 'student__user__last_name')

@admin.register(PaymentPlan)
class PaymentPlanAdmin(admin.ModelAdmin):
    list_display = ('student', 'total_amount', 'number_of_installments', 'installment_amount', 'status', 'created_by')
    list_filter = ('status', 'created_by')
    search_fields = ('student__user__first_name', 'student__user__last_name')

@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount', 'status', 'refund_method', 'requested_by', 'approved_by')
    list_filter = ('status', 'refund_method', 'requested_by')
    search_fields = ('student__user__first_name', 'student__user__last_name')
    actions = ['approve_refunds', 'reject_refunds']

    def approve_refunds(self, request, queryset):
        queryset.update(status='approved', approved_by=request.user)
    approve_refunds.short_description = "Approve selected refunds"

    def reject_refunds(self, request, queryset):
        queryset.update(status='rejected')
    reject_refunds.short_description = "Reject selected refunds"

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_type', 'student', 'amount', 'timestamp')
    list_filter = ('action_type', 'timestamp', 'user')
    search_fields = ('user__username', 'student__user__first_name', 'student__user__last_name')
    readonly_fields = ('timestamp',)

@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ('from_currency', 'to_currency', 'rate', 'date')
    list_filter = ('from_currency', 'to_currency', 'date')

@admin.register(BankReconciliation)
class BankReconciliationAdmin(admin.ModelAdmin):
    list_display = ('date', 'bank_balance', 'book_balance', 'difference', 'reconciled_by')
    list_filter = ('date', 'reconciled_by')

@admin.register(AgentPayment)
class AgentPaymentAdmin(admin.ModelAdmin):
    list_display = ('agent_name', 'student', 'amount', 'status', 'collected_at', 'recorded_by')
    list_filter = ('status', 'collected_at', 'recorded_by')
    search_fields = ('agent_name', 'student__user__first_name', 'student__user__last_name')
    actions = ['verify_agent_payments', 'mark_as_paid']

    def verify_agent_payments(self, request, queryset):
        queryset.update(status='verified')
    verify_agent_payments.short_description = "Verify selected agent payments"

    def mark_as_paid(self, request, queryset):
        queryset.update(status='paid')
    mark_as_paid.short_description = "Mark selected payments as paid to agent"
