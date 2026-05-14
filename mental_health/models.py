import uuid
from django.db import models
from django.contrib.auth.models import User


class Question(models.Model):
    id_question = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_positive = models.BooleanField(default=False)
    weight = models.FloatField(default=1.0)
    category = models.CharField(
        max_length=50,
        choices=[
            ("ansiedad", "Ansiedad"),
            ("depresion", "Depresión"),
            ("estres", "Estrés"),
            ("bienestar", "Bienestar"),
        ],
        default="bienestar"
    )
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'mh_question'
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['order']

    def __str__(self):
        return self.text
    

class ResponseOption(models.Model):
    id_response_option = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=50, unique=True)
    value = models.PositiveIntegerField()

    class Meta:
        db_table = 'mh_response_option'
        verbose_name = 'Response Option'
        verbose_name_plural = 'Response Options'
        ordering = ['value']

    def __str__(self):
        return f"{self.label} ({self.value})"


class EmotionalLevel(models.Model):
    id_emotional_level = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    min_score = models.PositiveIntegerField()
    max_score = models.PositiveIntegerField()
    color = models.CharField(max_length=20, unique=True)
    description = models.TextField()

    class Meta:
        db_table = 'mh_emotional_level'
        verbose_name = 'Emotional Level'
        verbose_name_plural = 'Emotional Levels'
        ordering = ['min_score']

    def __str__(self):
        return f"{self.name} ({self.min_score}-{self.max_score})"


class Intervention(models.Model):
    id_intervention = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    emotional_level = models.ForeignKey(
        EmotionalLevel,
        to_field='id_emotional_level',
        on_delete=models.CASCADE,
        related_name='interventions'
    )
    title = models.CharField(max_length=150)
    message = models.TextField()
    action = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'mh_intervention'
        verbose_name = 'Intervention'
        verbose_name_plural = 'Interventions'

    def __str__(self):
        return f"{self.title} - {self.emotional_level.name}"
    
from django.db import models


class Evaluation(models.Model):
    id_evaluation = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    text = models.TextField()
    score = models.IntegerField()
    emotional_level = models.ForeignKey(EmotionalLevel,on_delete=models.CASCADE,related_name='evaluations')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mh_evaluation'
        verbose_name = 'Evaluation'
        verbose_name_plural = 'Evaluations'

    def __str__(self):
        return f"{self.emotional_level.name} - {self.created_at}"
    

class EvaluationAnswer(models.Model):
    id_evaluation_answer = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    evaluation = models.ForeignKey(Evaluation,on_delete=models.CASCADE,related_name='answers')
    question = models.ForeignKey(Question,on_delete=models.CASCADE)
    response_option = models.ForeignKey(ResponseOption,on_delete=models.CASCADE)
    value = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mh_evaluation_answer'
        verbose_name = 'Evaluation Answer'
        verbose_name_plural = 'Evaluation Answers'

    def __str__(self):
        return f"{self.question.text} -> {self.response_option.label}"

class Profile(models.Model):
    id_profile = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name='profile')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    document_id = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    gender = models.CharField(max_length=10,choices=[('M', 'Masculino'),('F', 'Femenino'),('O', 'Otro')])
    age = models.PositiveIntegerField()
    location = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mh_profile'
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
class InterventionProgress(models.Model):

    id_progress = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    evaluation = models.ForeignKey(Evaluation,on_delete=models.CASCADE,related_name="progress")
    title = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    reflection = models.TextField(blank=True,null=True)
    completed_at = models.DateTimeField(null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "mh_intervention_progress"

    def __str__(self):
        return self.title