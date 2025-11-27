from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
from fees.models import (
    AcademicYear, Term, FeeComponent, FeeStructure,
    PaymentMethod, StudentLedger
)
from classes.models import Grade
from students.models import Student

class Command(BaseCommand):
    help = 'Populate initial fee data for the school'

    def handle(self, *args, **options):
        self.stdout.write('Populating fee data...')

        # Create academic year
        current_year, created = AcademicYear.objects.get_or_create(
            name='2025',
            defaults={
                'start_date': timezone.now().date().replace(month=1, day=1),
                'end_date': timezone.now().date().replace(month=12, day=31),
                'is_current': True
            }
        )
        if created:
            self.stdout.write(f'Created academic year: {current_year}')

        # Create terms
        terms_data = [
            {'name': 'term1', 'start_date': '2025-01-01', 'end_date': '2025-04-30'},
            {'name': 'term2', 'start_date': '2025-05-01', 'end_date': '2025-08-31'},
            {'name': 'term3', 'start_date': '2025-09-01', 'end_date': '2025-12-31'},
        ]

        for term_data in terms_data:
            term, created = Term.objects.get_or_create(
                name=term_data['name'],
                academic_year=current_year,
                defaults={
                    'start_date': term_data['start_date'],
                    'end_date': term_data['end_date'],
                    'is_current': term_data['name'] == 'term1'
                }
            )
            if created:
                self.stdout.write(f'Created term: {term}')

        # Create fee components
        components_data = [
            ('tuition', 'Tuition Fee', True),
            ('exam', 'Examination Fee', True),
            ('development', 'Development Levy', True),
            ('library', 'Library Fee', True),
            ('sports', 'Sports Levy', True),
        ]

        for comp_data in components_data:
            component, created = FeeComponent.objects.get_or_create(
                name=comp_data[0],
                defaults={
                    'description': comp_data[1],
                    'is_mandatory': comp_data[2],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'Created fee component: {component}')

        # Create payment methods
        payment_methods_data = [
            ('cash', 'Cash', True, False),
            ('ecocash', 'EcoCash', True, True),
            ('bank_transfer', 'Bank Transfer', True, True),
        ]

        for pm_data in payment_methods_data:
            pm, created = PaymentMethod.objects.get_or_create(
                name=pm_data[0],
                defaults={
                    'description': pm_data[1],
                    'is_active': pm_data[2],
                    'requires_reference': pm_data[3]
                }
            )
            if created:
                self.stdout.write(f'Created payment method: {pm}')

        # Create fee structures for existing grades
        current_term = Term.objects.filter(is_current=True).first()
        if current_term:
            grades = Grade.objects.all()
            for grade in grades:
                fee_structure, created = FeeStructure.objects.get_or_create(
                    academic_year=current_year,
                    term=current_term,
                    grade=grade,
                    is_day_scholar=True,
                    defaults={
                        'currency': 'USD',
                        'tuition_fee': Decimal('200.00'),
                        'exam_fee': Decimal('50.00'),
                        'development_levy': Decimal('30.00'),
                        'library_fee': Decimal('20.00'),
                        'sports_levy': Decimal('15.00'),
                        'payment_deadline': current_term.end_date,
                        'early_payment_discount': Decimal('5.00'),
                        'late_payment_penalty': Decimal('10.00'),
                    }
                )
                if created:
                    self.stdout.write(f'Created fee structure for {grade}: ${fee_structure.total_fee}')

        # Create student ledgers for existing students
        students = Student.objects.all()
        for student in students:
            ledger, created = StudentLedger.objects.get_or_create(
                student=student,
                academic_year=current_year,
                term=current_term,
                defaults={
                    'term_fees': Decimal('315.00'),  # Sum of fees above
                    'payments_made': Decimal('0.00'),
                }
            )
            if created:
                ledger.update_balances()
                self.stdout.write(f'Created ledger for {student}')

        self.stdout.write(self.style.SUCCESS('Successfully populated fee data!'))