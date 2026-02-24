from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth import get_user_model
from .models import Voter, Candidate, Vote
from .serializers import CandidateSerializer
import requests
import json
import base64


User = get_user_model()

@csrf_exempt
def officer_login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')

        try:
            officer = User.objects.get(username=username)
            if officer.check_password(password):
                return JsonResponse({'status': 'success', 'message': 'Login successful'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid credentials'}, status=401)
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)

@csrf_exempt
def verify_voter(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        voter_id = data.get('voter_id')
        if not voter_id:
            return JsonResponse({"message": "Voter ID is required"}, status=400)
        
        try:
            voter = Voter.objects.get(voter_id=voter_id)
        except Voter.DoesNotExist:
            return JsonResponse({"message": "Voter not found"}, status=404)
        
        if Vote.objects.filter(voter=voter).exists():
            return JsonResponse({"message": "Voter has already voted"}, status=403)

        return JsonResponse({"message": "Voter found", "name": voter.name}, status=200)

@csrf_exempt
@require_http_methods(["POST"])
def verify_fingerprint(request):
    try:
        data = json.loads(request.body)
        voter_id = data.get("voter_id")
        fingerprint_b64 = data.get("fingerprint_template")
        file = None

        if not voter_id or (not fingerprint_b64):
            return JsonResponse({"error": "Missing voter_id or fingerprint."}, status=400)

        if file:
            fingerprint_bytes = file.read()
            fingerprint_b64 = base64.b64encode(fingerprint_bytes).decode("utf-8")

        try:
            voter = Voter.objects.get(voter_id=voter_id)
            stored_b64 = voter.fingerprint_template
        except ObjectDoesNotExist:
            return JsonResponse({"error": "Voter not found."}, status=404)

        payload = {
            "ProbTemplate": fingerprint_b64,
            "GalleryTemplate": stored_b64,
            "BioType": "ANSI"
        }

        sdk_url = "http://localhost:8004/mfs100/verify"
        sdk_response = requests.post(sdk_url, json=payload, timeout=5)

        if sdk_response.status_code == 200:
            result = sdk_response.json()
            match = result.get("Status", False) is True
            return JsonResponse({"status": "match" if match else "no-match"})
        else:
            return JsonResponse({"error": "SDK verification failed."}, status=502)

    except Exception as e:
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)

@csrf_exempt
def get_candidates(request):
    if request.method == 'GET':
        try:
            candidates = Candidate.objects.all()

            if not candidates:
                return JsonResponse({"message": "No candidates found"}, status=404)

            serializer = CandidateSerializer(candidates, many=True)

            return JsonResponse(serializer.data, safe=False, status=200)

        except Exception as e:
            return JsonResponse({"message": f"An error occurred: {str(e)}"}, status=500)

    return JsonResponse({"message": "Method not allowed"}, status=405)

@csrf_exempt
def submit_vote(request):
    if request.method != 'POST':
        return JsonResponse({"message": "Invalid request method"}, status=405)

    try:
        data = json.loads(request.body)
        voter_id = data.get('voter_id')
        candidate_id = data.get('candidate_id')  

        if not voter_id or not candidate_id:
            return JsonResponse({"message": "voter_id and candidate_id are required"}, status=400)

        voter = Voter.objects.get(voter_id=voter_id)
        candidate = Candidate.objects.get(id=candidate_id)

        Vote.objects.create(voter=voter, candidate=candidate)
        return JsonResponse({"message": "Vote submitted"}, status=200)

    except Voter.DoesNotExist:
        return JsonResponse({"message": "Voter not found"}, status=404)
    except Candidate.DoesNotExist:
        return JsonResponse({"message": "Candidate not found"}, status=404)
    except Exception as e:
        return JsonResponse({"message": "Error submitting vote"}, status=400)

