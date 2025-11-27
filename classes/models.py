from django.db import models

class Grade(models.Model):
    name = models.CharField(max_length=20, unique=True)  # e.g., ECD A, Grade 1, etc.

    def __str__(self):
        return self.name

class ClassRoom(models.Model):
    name = models.CharField(max_length=10)  # e.g., A, B, C
    grade = models.ForeignKey(Grade, on_delete=models.CASCADE, related_name='classrooms')

    def __str__(self):
        return self.name

class Teacher(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE)
    assigned_grades = models.ManyToManyField(Grade, blank=True)
    assigned_classes = models.ManyToManyField(ClassRoom, blank=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
