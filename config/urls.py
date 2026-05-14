from django.contrib import admin
from django.urls import path, include
from django.urls import path
from rest_framework_simplejwt.views import (TokenObtainPairView,TokenRefreshView,)
from mental_health.views import get_history

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('mental_health.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]