from django.urls import path
from . import views

urlpatterns = [
    path('candidates/', views.get_candidates),
    path('verify-voter/', views.verify_voter),
    path('verify-fingerprint/', views.verify_fingerprint),
    path('submit-vote/', views.submit_vote),
    path('officer-login/', views.officer_login),
]
