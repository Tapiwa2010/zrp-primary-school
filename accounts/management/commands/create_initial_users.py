from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from classes.models import Grade, ClassRoom, Teacher
from fees.models import FeeStructure, StudentFeeBalance
from students.models import Student

User = get_user_model()

class Command(BaseCommand):
    help = 'Create initial admin and teacher users, and sample grades/classrooms'

    def handle(self, *args, **options):
        # Create admin user
        if not User.objects.filter(email='admin@school.com').exists():
            admin = User.objects.create_user(
                username='admin@school.com',
                email='admin@school.com',
                password='admin123',
                first_name='School',
                last_name='Admin',
                role='admin',
                is_staff=True,
                is_superuser=True
            )
            self.stdout.write(self.style.SUCCESS('Admin user created: admin@school.com/admin123'))

        # Create teacher user
        if not User.objects.filter(email='teacher@school.com').exists():
            teacher = User.objects.create_user(
                username='teacher@school.com',
                email='teacher@school.com',
                password='teacher123',
                first_name='John',
                last_name='Doe',
                role='teacher'
            )
            self.stdout.write(self.style.SUCCESS('Teacher user created: teacher@school.com/teacher123'))

        # Create sample grades
        grades_data = ['ECD A', 'ECD B', 'Grade 1', 'Grade 2', 'Grade 3', 'Grade 4', 'Grade 5', 'Grade 6', 'Grade 7']
        for grade_name in grades_data:
            grade, created = Grade.objects.get_or_create(name=grade_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Grade created: {grade_name}'))

        # Create classrooms A, B, C, D for each grade
        for grade in Grade.objects.all():
            for class_name in ['A', 'B', 'C', 'D']:
                classroom, created = ClassRoom.objects.get_or_create(name=class_name, grade=grade)
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Classroom created: {grade.name} {class_name}'))

        # Create fee structures
        fee_data = {
            'ECD A': {'tuition': 50, 'exam': 10, 'activity': 5},
            'ECD B': {'tuition': 50, 'exam': 10, 'activity': 5},
            'Grade 1': {'tuition': 100, 'exam': 20, 'activity': 10},
            'Grade 2': {'tuition': 120, 'exam': 25, 'activity': 12},
            'Grade 3': {'tuition': 140, 'exam': 30, 'activity': 15},
            'Grade 4': {'tuition': 160, 'exam': 35, 'activity': 18},
            'Grade 5': {'tuition': 180, 'exam': 40, 'activity': 20},
            'Grade 6': {'tuition': 200, 'exam': 45, 'activity': 25},
            'Grade 7': {'tuition': 220, 'exam': 50, 'activity': 30},
        }

        for grade_name, fees in fee_data.items():
            try:
                grade = Grade.objects.get(name=grade_name)
                fee_structure, created = FeeStructure.objects.get_or_create(
                    grade=grade,
                    defaults={
                        'tuition_fee': fees['tuition'],
                        'exam_fee': fees['exam'],
                        'activity_fee': fees['activity']
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Fee structure created for {grade_name}: ${fee_structure.total_fee}'))
            except Grade.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Grade {grade_name} not found, skipping fee structure'))

        # Create fee balances for existing students
        for student in Student.objects.all():
            try:
                grade = student.grade
                fee_structure = FeeStructure.objects.get(grade=grade)
                balance, created = StudentFeeBalance.objects.get_or_create(
                    student=student,
                    defaults={'total_fees': fee_structure.total_fee}
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'Fee balance created for {student}: ${balance.total_fees}'))
            except FeeStructure.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'No fee structure for grade {grade.name}'))

        # Assign teacher to all classes
        try:
            teacher_user = User.objects.get(email='teacher@school.com')
            teacher_profile, created = Teacher.objects.get_or_create(user=teacher_user)
            if created:
                teacher_profile.assigned_grades.set(Grade.objects.all())
                teacher_profile.assigned_classes.set(ClassRoom.objects.all())
                self.stdout.write(self.style.SUCCESS('Teacher assigned to all grades and classes'))
        except User.DoesNotExist:
            self.stdout.write(self.style.WARNING('Teacher user not found'))

        self.stdout.write(self.style.SUCCESS('Initial setup complete!'))