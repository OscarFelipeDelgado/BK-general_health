from django.contrib import admin
from .models import InterventionProgress, Question, ResponseOption, EmotionalLevel, Intervention, Evaluation, EvaluationAnswer

admin.site.register(Question)
admin.site.register(ResponseOption)
admin.site.register(EmotionalLevel)
admin.site.register(Intervention)
admin.site.register(Evaluation)
admin.site.register(EvaluationAnswer)
admin.site.register(InterventionProgress)