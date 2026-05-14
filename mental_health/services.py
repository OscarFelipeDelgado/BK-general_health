from mental_health.models import EmotionalLevel


def calculate_emotional_level(total_score: int):
    """
    Recibe el puntaje total del usuario y retorna
    el nivel emocional correspondiente.
    """
    return EmotionalLevel.objects.filter(
        min_score__lte=total_score,
        max_score__gte=total_score
    ).first()


def build_result(total_score, category_scores, interpretation):

    anxiety = category_scores.get("ansiedad", 0)
    stress = category_scores.get("estres", 0)
    depression = category_scores.get("depresion", 0)

    # 🔥 bienestar positivo real
    wellbeing = category_scores.get("bienestar", 0)

    scores = {
        "bienestar": wellbeing,
        "ansiedad": anxiety,
        "estres": stress,
        "depresion": depression
    }

    dominant = max(scores, key=scores.get)

    # =========================
    # 🔵 ESTADO CRÍTICO
    # =========================

    critical_count = 0

    if anxiety >= 85:
        critical_count += 1

    if stress >= 85:
        critical_count += 1

    if depression >= 85:
        critical_count += 1

    # 🔥 3 dimensiones muy elevadas
    if critical_count >= 3 and wellbeing <= 30:

        return {
            "level": "Crítico",
            "color": "#34495e",
            "progress": 100,
            "title": "Atención emocional prioritaria",
            "message": "Se identifican múltiples indicadores emocionales elevados que podrían estar afectando significativamente tu bienestar actual.",
            "secondary_message": "Este resultado refleja cómo te has sentido recientemente y puede ser una oportunidad para buscar apoyo emocional.",
            "interpretation": interpretation["analysis"],
            "recommendations": interpretation["alerts"]
        }

    # =========================
    # 🟢 BIENESTAR
    # =========================
    if dominant == "bienestar":

        return {
            "level": "Verde",
            "color": "#2ecc71",
            "progress": wellbeing,
            "title": "Bienestar emocional estable",
            "message": "Predomina un estado emocional positivo.",
            "interpretation": interpretation["analysis"],
            "recommendations": interpretation["alerts"]
        }

    # =========================
    # 🟡 ANSIEDAD
    # =========================
    elif dominant == "ansiedad":

        return {
            "level": "Amarillo",
            "color": "#f1c40f",
            "progress": anxiety,
            "title": "Ansiedad predominante",
            "message": "Se observan señales predominantes de ansiedad.",
            "interpretation": interpretation["analysis"],
            "recommendations": interpretation["alerts"]
        }

    # =========================
    # 🟠 ESTRÉS
    # =========================
    elif dominant == "estres":

        return {
            "level": "Naranja",
            "color": "#e67e22",
            "progress": stress,
            "title": "Estrés predominante",
            "message": "Se evidencia una carga importante de estrés.",
            "interpretation": interpretation["analysis"],
            "recommendations": interpretation["alerts"]
        }

    # =========================
    # 🟣 DEPRESIÓN
    # =========================
    else:

        return {
            "level": "Morado",
            "color": "#8e44ad",
            "progress": depression,
            "title": "Desánimo emocional predominante",
            "message": "Se identifican señales asociadas a desánimo emocional.",
            "interpretation": interpretation["analysis"],
            "recommendations": interpretation["alerts"]
        }


def calculate_total_score(processed_answers):

    total_negative = 0
    total_wellbeing = 0

    MAX_OPTION_VALUE = 4

    for item in processed_answers:

        question = item["question"]
        option = item["option"]

        # 🔥 preguntas positivas
        if question.is_positive:

            adjusted_value = option.value

        # 🔥 preguntas negativas
        else:

            adjusted_value = (
                MAX_OPTION_VALUE - option.value
            )

        value = adjusted_value * question.weight

        # 🔴 categorías negativas
        if question.category in [
            "ansiedad",
            "estres",
            "depresion"
        ]:

            total_negative += value

        # 🟢 bienestar positivo
        elif question.category == "bienestar":

            total_wellbeing += value

    # 🔥 bienestar reduce carga emocional
    final_score = total_negative - total_wellbeing

    # evitar negativos
    if final_score < 0:
        final_score = 0

    return round(final_score)


def calculate_category_scores(processed_answers):

    scores = {}
    max_scores = {}

    MAX_OPTION_VALUE = 4

    for item in processed_answers:

        question = item["question"]
        option = item["option"]

        category = question.category

        if category not in scores:
            scores[category] = 0
            max_scores[category] = 0

        # 🟢 PREGUNTAS POSITIVAS
        # Mientras más alto responda el usuario,
        # mayor bienestar emocional
        if question.is_positive:

            adjusted_value = option.value

        # 🔴 PREGUNTAS NEGATIVAS
        # Mientras más alto responda,
        # mayor carga emocional
        else:

            adjusted_value = option.value

        # 🔥 aplicar peso
        weighted_value = (
            adjusted_value * question.weight
        )

        max_weighted = (
            MAX_OPTION_VALUE * question.weight
        )

        scores[category] += weighted_value
        max_scores[category] += max_weighted

    normalized_scores = {}

    for category in scores:

        if max_scores[category] == 0:
            normalized_scores[category] = 0
            continue

        percentage = (
            scores[category] / max_scores[category]
        ) * 100

        normalized_scores[category] = round(
            min(max(percentage, 0), 100)
        )

    return normalized_scores


def interpret_emotional_profile(category_scores):
    """
    Analiza el perfil emocional por dimensiones
    y devuelve interpretación clínica básica
    """

    analysis = []
    alerts = []

    ansiedad = category_scores.get("ansiedad", 0)
    estres = category_scores.get("estres", 0)
    depresion = category_scores.get("depresion", 0)
    bienestar = category_scores.get("bienestar", 0)

    # ANSIEDAD
    if ansiedad >= 70:
        analysis.append(
            "Se detecta un nivel elevado de ansiedad."
        )
        alerts.append("Alta ansiedad")

    elif ansiedad >= 40:
        analysis.append(
            "Se observan señales moderadas de ansiedad."
        )

    # ESTRÉS
    if estres >= 70:
        analysis.append(
            "Se evidencia una carga significativa de estrés."
        )
        alerts.append("Estrés alto")

    elif estres >= 40:
        analysis.append(
            "Se observan señales moderadas de estrés."
        )

    # DEPRESIÓN
    if depresion >= 70:
        analysis.append(
            "Se identifican signos relevantes de desánimo o bajo estado de ánimo."
        )
        alerts.append("Riesgo depresivo")

    elif depresion >= 40:
        analysis.append(
            "Se observan señales moderadas de desánimo emocional."
        )

    # BIENESTAR
    if bienestar >= 70:
        analysis.append(
            "Se observan indicadores positivos de bienestar emocional."
        )

    elif bienestar <= 30:
        analysis.append(
            "Se observa una disminución en indicadores de bienestar emocional."
        )
        alerts.append("Bienestar bajo")

    # BALANCE GENERAL
    carga_negativa = (
        ansiedad +
        estres +
        depresion
    ) / 3

    if carga_negativa > bienestar:
        analysis.append(
            "El balance emocional general indica mayor carga negativa que positiva."
        )

    return {
        "analysis": analysis,
        "alerts": alerts
    }