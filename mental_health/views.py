from django.utils import timezone
import re
import json

from django.db import IntegrityError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from mental_health.services import calculate_category_scores
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .services import calculate_total_score, build_result
from .models import (Evaluation,EmotionalLevel,EvaluationAnswer, InterventionProgress,Question,ResponseOption,Profile)
from mental_health.services import interpret_emotional_profile
from mental_health.intervention_engine import build_intervention_plan
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password

# =========================
# 🧠 EVALUACIÓN
# =========================
@csrf_exempt
def evaluate_emotional_state(request):
    print("🚀 ENTRÓ A ESTA FUNCIÓN", flush=True)

    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        body = json.loads(request.body)
        request_answers = body.get("answers", [])

        if not isinstance(request_answers, list) or len(request_answers) == 0:
            return JsonResponse({"error": "Respuestas inválidas"}, status=400)

        processed_answers = []

        for answer in request_answers:
            question = Question.objects.filter(
                id_question=answer.get("question_id")
            ).first()

            option = ResponseOption.objects.filter(
                id_response_option=answer.get("response_option_id")
            ).first()

            if not question or not option:
                return JsonResponse({"error": "Datos inválidos en respuestas"}, status=400)

            processed_answers.append({
                "question": question,
                "option": option
            })

        total_score = calculate_total_score(processed_answers)

        category_scores = calculate_category_scores(processed_answers)
        print("CATEGORY SCORES:", category_scores, flush=True)


        interpretation = interpret_emotional_profile(category_scores)

        # 🧠 construir resultado (una sola fuente de verdad)
        result = build_result(
            total_score=total_score,
            category_scores=category_scores,
            interpretation=interpretation
        )

        # 🧠 construir plan de intervención psicológica
        interventions = build_intervention_plan(
            level=result["level"],
            category_scores=category_scores
        )

        emotional_level = EmotionalLevel.objects.filter(
            name=result["level"]
        ).first()

        if not emotional_level:
            return JsonResponse({"error": "Nivel emocional no definido"}, status=400)

        # 💾 guardar evaluación
        evaluation = Evaluation.objects.create(
            text=json.dumps(request_answers),
            score=total_score,
            emotional_level=emotional_level
        )

        # 💾 guardar respuestas
        for ans in processed_answers:
            EvaluationAnswer.objects.create(
                evaluation=evaluation,
                question=ans["question"],
                response_option=ans["option"],
                value=ans["option"].value
            )

        # ✅ RESPUESTA FINAL
        return JsonResponse({
            "id": str(evaluation.id_evaluation),
            "score": total_score,
            "category_scores": category_scores,
            "analysis": interpretation["analysis"],
            "alerts": interpretation["alerts"],
            "interventions": interventions,
            **result
        }, status=200)

    except Exception as e:
        print("🔥 ERROR BACKEND:", str(e), flush=True)
        return JsonResponse({"error": str(e)}, status=400)


# =========================
# 📊 HISTORIAL
# =========================
@csrf_exempt
def get_history(request):
    if request.method != "GET":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        evaluations = Evaluation.objects.all().order_by('-created_at')

        data = []

        for e in evaluations:
            data.append({
                "id": str(e.id_evaluation),
                "score": e.score,
                "level": e.emotional_level.name,
                "color": e.emotional_level.color,
                "description": e.emotional_level.description,
                "created_at": e.created_at,
                "answers": [
                    {
                        "question": ans.question.text,
                        "response": ans.response_option.label,
                        "value": ans.value
                    }
                    for ans in e.answers.all()
                ]
            })

        return JsonResponse(data, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# =========================
# 📈 DASHBOARD
# =========================
@csrf_exempt
def get_dashboard(request):
    if request.method != "GET":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        evaluations = Evaluation.objects.all()

        total = evaluations.count()

        avg_score = 0
        if total > 0:
            avg_score = sum(e.score for e in evaluations) / total

        levels = {}

        for e in evaluations:
            name = e.emotional_level.name
            levels[name] = levels.get(name, 0) + 1

        result = {
            "total_evaluations": total,
            "average_score": round(avg_score, 2),
            "levels": levels
        }

        return JsonResponse(result, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# =========================
# ❓ PREGUNTAS
# =========================

def get_questions(request):
    if request.method != "GET":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    try:
        questions = Question.objects.filter(is_active=True).order_by("order")
        options = ResponseOption.objects.all().order_by("value")

        data = []

        for q in questions:
            data.append({
                "id": str(q.id_question),
                "text": q.text,

                "category": q.category,

                "options": [
                    {
                        "id": str(opt.id_response_option),
                        "label": opt.label,
                        "value": opt.value
                    }
                    for opt in options
                ]
            })

        return JsonResponse(data, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)

# =========================
# 👤 PERFIL (🔥 ARREGLADO)
# =========================
# =========================
# 👤 PERFIL
# =========================
@api_view(['GET', 'POST', 'PUT'])
@permission_classes([IsAuthenticated])
def save_profile(request):

    print("USER:", request.user)
    print("AUTH:", request.auth)

    try:

        # =====================================
        # 🔵 OBTENER PERFIL
        # =====================================
        if request.method == "GET":

            profile = Profile.objects.filter(
                user=request.user
            ).first()

            if not profile:
                return Response(
                    {"error": "Perfil no encontrado"},
                    status=404
                )

            return Response({
                "username": request.user.username,
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "document_id": profile.document_id,
                "phone": profile.phone,
                "email": profile.email,
                "gender": profile.gender,
                "age": profile.age,
                "location": profile.location
            })

        # =====================================
        # 🔵 CREAR / ACTUALIZAR
        # =====================================
        body = request.data

        first_name = body.get("first_name", "").strip()
        last_name = body.get("last_name", "").strip()
        document_id = body.get("document_id", "").strip()
        phone = body.get("phone", "").strip()
        email = body.get("email", "").strip()
        gender = body.get("gender", "").strip()
        age = body.get("age")
        location = body.get("location", "").strip()

        # 🔴 VALIDACIONES
        if not all([
            first_name,
            last_name,
            document_id,
            phone,
            email,
            gender,
            age,
            location
        ]):
            return Response(
                {"error": "Todos los campos son obligatorios"},
                status=400
            )

        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$', first_name):
            return Response(
                {"error": "El nombre solo debe contener letras"},
                status=400
            )

        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$', last_name):
            return Response(
                {"error": "El apellido solo debe contener letras"},
                status=400
            )

        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ ]+$', location):
            return Response(
                {"error": "La ciudad solo debe contener letras"},
                status=400
            )

        if not re.match(r'^[a-zA-Z0-9]+$', document_id):
            return Response(
                {"error": "El documento solo debe contener letras y números"},
                status=400
            )

        if not phone.isdigit():
            return Response(
                {"error": "El celular solo debe contener números"},
                status=400
            )

        try:
            age = int(age)

            if age <= 0:
                return Response(
                    {"error": "Edad inválida"},
                    status=400
                )

        except:
            return Response(
                {"error": "La edad debe ser numérica"},
                status=400
            )

        if "@" not in email:
            return Response(
                {"error": "Correo inválido"},
                status=400
            )

        # 🔴 VALIDAR DUPLICADOS
        if Profile.objects.filter(
            email=email
        ).exclude(user=request.user).exists():

            return Response(
                {"error": "El correo ya está registrado"},
                status=400
            )

        if Profile.objects.filter(
            document_id=document_id
        ).exclude(user=request.user).exists():

            return Response(
                {"error": "El documento ya está registrado"},
                status=400
            )

        # 🔵 GUARDAR / ACTUALIZAR
        profile, created = Profile.objects.update_or_create(
            user=request.user,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "document_id": document_id,
                "phone": phone,
                "email": email,
                "gender": gender,
                "age": age,
                "location": location,
            }
        )

        return Response({
            "message": "Perfil guardado correctamente"
        }, status=200)

    except Exception as e:

        print("🔥 ERROR BACKEND:", str(e))

        return Response(
            {"error": str(e)},
            status=400
        )


# =========================
# ✅ VALIDAR PERFIL
# =========================
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_profile(request):
    exists = Profile.objects.filter(user=request.user).exists()
    return Response({"has_profile": exists})


# =========================
# 🟢 REGISTER
# =========================
@api_view(['POST'])
def register_user(request):

    try:
        body = request.data

        username = body.get("username", "").strip()
        password = body.get("password", "").strip()

        first_name = body.get("first_name", "").strip()
        last_name = body.get("last_name", "").strip()
        document_id = body.get("document_id", "").strip()
        phone = body.get("phone", "").strip()
        email = body.get("email", "").strip()
        gender = body.get("gender", "").strip()
        age = body.get("age")
        location = body.get("location", "").strip()

        # =========================
        # VALIDACIONES
        # =========================
        if not username or not password:
            return Response(
                {"error": "Usuario y contraseña obligatorios"},
                status=400
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "El usuario ya existe"},
                status=400
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "El correo ya está registrado"},
                status=400
            )

        if Profile.objects.filter(document_id=document_id).exists():
            return Response(
                {"error": "El documento ya existe"},
                status=400
            )

        # =========================
        # CREAR USUARIO
        # =========================
        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password)
        )

        # =========================
        # CREAR PERFIL
        # =========================
        Profile.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            document_id=document_id,
            phone=phone,
            email=email,
            gender=gender,
            age=age,
            location=location
        )

        return Response({
            "message": "Usuario registrado correctamente"
        }, status=201)

    except Exception as e:
        return Response({
            "error": str(e)
        }, status=400)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):

    try:

        profile = Profile.objects.filter(
            user=request.user
        ).first()

        if not profile:
            return Response(
                {"error": "Perfil no encontrado"},
                status=404
            )

        return Response({
            "username": request.user.username,
            "first_name": profile.first_name,
            "last_name": profile.last_name,
            "document_id": profile.document_id,
            "phone": profile.phone,
            "email": profile.email,
            "gender": profile.gender,
            "age": profile.age,
            "location": profile.location
        })

    except Exception as e:

        return Response({
            "error": str(e)
        }, status=400)
    
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):

    try:

        profile = Profile.objects.filter(
            user=request.user
        ).first()

        if not profile:
            return Response({
                "error": "Perfil no encontrado"
            }, status=404)

        data = request.data

        profile.first_name = data.get("first_name")
        profile.last_name = data.get("last_name")
        profile.document_id = data.get("document_id")
        profile.phone = data.get("phone")
        profile.email = data.get("email")
        profile.gender = data.get("gender")
        profile.age = data.get("age")
        profile.location = data.get("location")

        profile.save()

        return Response({
            "message": "Perfil actualizado"
        })

    except Exception as e:

        return Response({
            "error": str(e)
        }, status=400)
    
@csrf_exempt
def complete_intervention(request):

    if request.method != "POST":
        return JsonResponse(
            {"error": "Método no permitido"},
            status=405
        )

    try:

        body = json.loads(request.body)

        evaluation_id = body.get("evaluation_id")
        title = body.get("title")

        progress, created = InterventionProgress.objects.get_or_create(
            evaluation_id=evaluation_id,
            title=title
        )

        progress.completed = True
        progress.completed_at = timezone.now()

        progress.save()

        return JsonResponse({
            "message": "Actividad completada"
        })

    except Exception as e:

        return JsonResponse({
            "error": str(e)
        }, status=400)
    
@csrf_exempt
def save_reflection(request):

    if request.method != "POST":
        return JsonResponse(
            {"error": "Método no permitido"},
            status=405
        )

    try:

        body = json.loads(request.body)

        evaluation_id = body.get("evaluation_id")
        reflection = body.get("reflection")

        progresses = InterventionProgress.objects.filter(
            evaluation_id=evaluation_id
        )

        progresses.update(
            reflection=reflection
        )

        return JsonResponse({
            "message": "Reflexión guardada"
        })

    except Exception as e:

        return JsonResponse({
            "error": str(e)
        }, status=400)
    