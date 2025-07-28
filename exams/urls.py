from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'exams', views.ExamViewSet)
router.register(r'questions', views.QuestionViewSet)
router.register(r'student-exams', views.StudentExamViewSet)

urlpatterns = [
    path('', include(router.urls)),
]