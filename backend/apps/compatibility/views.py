from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime
from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.tokens import RefreshToken

from apps.companies.models import CompanyProfile, CompanyReview
from apps.candidates.models import CandidateProfile
from apps.vacancies.models import Vacancy
from apps.applications.models import Application
from apps.tests_app.models import TestSchedule, TestCandidateAssignment
from apps.feedback.models import Feedback
from apps.complaints.models import Complaint

User = get_user_model()


@extend_schema(tags=['Flutter Compatibility'])
class LegacyUserLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        username_or_email = request.data.get('Username') or request.data.get('username')
        password = request.data.get('Password') or request.data.get('password')

        if not username_or_email or not password:
            return Response({
                'status': 'no',
                'message': 'Username/Email and password are required.'
            })

        user = authenticate(request, username=username_or_email, password=password)
        if user is None:
            return Response({
                'status': 'no',
                'message': 'Invalid credentials.'
            })

        if not user.is_active:
            return Response({
                'status': 'no',
                'message': 'Account is deactivated.'
            })

        if getattr(user, 'role', '') == User.Role.COMPANY:
            company = getattr(user, 'company_profile', None)
            if company and company.verification_status != CompanyProfile.VerificationStatus.APPROVED:
                return Response({
                    'status': 'no',
                    'message': f'Company verification {company.verification_status}. Access restricted until approved.'
                })

        role_str = user.role.lower() if hasattr(user, 'role') else 'user'
        if user.is_staff or getattr(user, 'role', '') == 'ADMIN':
            role_str = 'admin'
        elif getattr(user, 'role', '') == 'COMPANY':
            role_str = 'company'
        else:
            role_str = 'user'

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({
            'status': 'ok',
            'lid': str(user.id),
            'token': access_token,
            'access': access_token,
            'refresh': str(refresh),
            'type': role_str,
            'role': role_str
        })


@extend_schema(tags=['Flutter Compatibility'])
class LegacyUserRegistrationView(APIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, *args, **kwargs):
        name = request.data.get('name', '').strip()
        email = request.data.get('email', '').strip()
        phone = request.data.get('phone', '').strip()
        dob_raw = request.data.get('dob', '').strip()
        gender = request.data.get('gender', '').strip()
        place = request.data.get('place', '').strip()
        post = request.data.get('post', '').strip()
        city = request.data.get('city', '').strip()
        state = request.data.get('state', '').strip()
        pin = request.data.get('pin', '').strip()
        qualification = request.data.get('qualification', '').strip()
        password = request.data.get('password', '')

        photo_file = request.FILES.get('photo')
        resume_file = request.FILES.get('resume')

        if not email or not password or not name:
            return Response({'status': 'no', 'message': 'Name, email, and password are required.'})

        if User.objects.filter(email=email).exists():
            return Response({'status': 'no', 'message': 'An account with this email already exists.'})

        username = email.split('@')[0]
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        try:
            validate_password(password)
        except ValidationError as e:
            return Response({'status': 'no', 'message': '; '.join(e.messages)})

        dob = None
        if dob_raw:
            for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d'):
                try:
                    dob = datetime.strptime(dob_raw, fmt).date()
                    break
                except ValueError:
                    continue

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=User.Role.CANDIDATE
        )

        candidate = CandidateProfile.objects.create(
            user=user,
            full_name=name,
            phone=phone,
            dob=dob,
            gender=gender,
            place=place,
            post=post,
            city=city,
            state=state,
            pin=pin,
            qualifications=qualification,
        )

        if photo_file:
            candidate.photo = photo_file
        if resume_file:
            candidate.resume = resume_file
        candidate.save()

        return Response({
            'status': 'ok',
            'message': 'Registration successful',
            'lid': str(user.id)
        })


@extend_schema(tags=['Flutter Compatibility'])
class LegacyUserProfileView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        lid = request.data.get('lid')
        if not lid:
            return Response({'status': 'no', 'message': 'lid is required.'})

        try:
            candidate = CandidateProfile.objects.select_related('user').get(user__id=lid)
        except CandidateProfile.DoesNotExist:
            return Response({'status': 'no', 'message': 'Candidate profile not found.'})

        photo_url = ""
        if candidate.photo:
            try:
                photo_url = request.build_absolute_uri(candidate.photo.url)
            except Exception:
                photo_url = str(candidate.photo)

        resume_url = ""
        if candidate.resume:
            try:
                resume_url = request.build_absolute_uri(candidate.resume.url)
            except Exception:
                resume_url = str(candidate.resume)

        payload = {
            'status': 'ok',
            'name': candidate.full_name or '',
            'email': candidate.user.email or '',
            'phone': candidate.phone or '',
            'dob': str(candidate.dob) if candidate.dob else '',
            'gender': candidate.gender or '',
            'place': candidate.place or '',
            'post': candidate.post or '',
            'city': candidate.city or '',
            'state': candidate.state or '',
            'pin': candidate.pin or '',
            'qualification': candidate.qualifications or '',
            'skills': candidate.skills or '',
            'experience': str(candidate.experience_years),
            'photo': photo_url,
            'resume': resume_url,
        }
        # Provide both flattened keys and 'data' array for compatibility
        payload['data'] = [{k: v for k, v in payload.items() if k != 'data'}]
        return Response(payload)


@extend_schema(tags=['Flutter Compatibility'])
class LegacyUserProfileViewForEditView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        lid = request.data.get('lid')
        if not lid:
            return Response({'status': 'no', 'message': 'lid is required.'})

        try:
            candidate = CandidateProfile.objects.select_related('user').get(user__id=lid)
        except CandidateProfile.DoesNotExist:
            return Response({'status': 'no', 'message': 'Candidate profile not found.'})

        photo_url = ""
        if candidate.photo:
            try:
                photo_url = request.build_absolute_uri(candidate.photo.url)
            except Exception:
                photo_url = str(candidate.photo)

        payload = {
            'status': 'ok',
            'name': candidate.full_name or '',
            'email': candidate.user.email or '',
            'phone': candidate.phone or '',
            'dob': str(candidate.dob) if candidate.dob else '',
            'gender': candidate.gender or '',
            'place': candidate.place or '',
            'post': candidate.post or '',
            'city': candidate.city or '',
            'state': candidate.state or '',
            'pin': candidate.pin or '',
            'qualification': candidate.qualifications or '',
            'photo': photo_url,
        }
        payload['data'] = {k: v for k, v in payload.items() if k != 'data'}
        return Response(payload)


@extend_schema(tags=['Flutter Compatibility'])
class LegacyUserEditProfileView(APIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, *args, **kwargs):
        lid = request.data.get('lid')
        if not lid:
            return Response({'status': 'no', 'message': 'lid is required.'})

        try:
            candidate = CandidateProfile.objects.select_related('user').get(user__id=lid)
        except CandidateProfile.DoesNotExist:
            return Response({'status': 'no', 'message': 'Candidate profile not found.'})

        if 'name' in request.data:
            candidate.full_name = request.data['name'].strip()
        if 'email' in request.data:
            candidate.user.email = request.data['email'].strip()
            candidate.user.save()
        if 'phone' in request.data:
            candidate.phone = request.data['phone'].strip()
        if 'gender' in request.data:
            candidate.gender = request.data['gender'].strip()
        if 'place' in request.data:
            candidate.place = request.data['place'].strip()
        if 'post' in request.data:
            candidate.post = request.data['post'].strip()
        if 'city' in request.data:
            candidate.city = request.data['city'].strip()
        if 'state' in request.data:
            candidate.state = request.data['state'].strip()
        if 'pin' in request.data:
            candidate.pin = request.data['pin'].strip()
        if 'qualification' in request.data:
            candidate.qualifications = request.data['qualification'].strip()

        dob_raw = request.data.get('dob')
        if dob_raw:
            for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y', '%Y/%m/%d'):
                try:
                    candidate.dob = datetime.strptime(dob_raw.strip(), fmt).date()
                    break
                except ValueError:
                    continue

        if 'photo' in request.FILES:
            candidate.photo = request.FILES['photo']
        if 'resume' in request.FILES:
            candidate.resume = request.FILES['resume']

        candidate.save()

        return Response({
            'status': 'ok',
            'message': 'Profile updated successfully.'
        })


@extend_schema(tags=['Flutter Compatibility'])
class LegacyCompanyDropdownView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        companies = CompanyProfile.objects.all().order_by('company_name')

        data = [{'id': str(c.id), 'name': c.company_name} for c in companies]
        return Response({
            'status': 'ok',
            'data': data
        })


@extend_schema(tags=['Flutter Compatibility'])
class LegacyReviewCompanyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        lid = request.data.get('lid')
        company_id = request.data.get('Company_id') or request.data.get('company_id')
        rating_str = request.data.get('rating', '5.0')
        review_text = request.data.get('review', '').strip()

        if not review_text:
            return Response({'status': 'no', 'message': 'Review text is required.'})

        if not company_id:
            return Response({'status': 'no', 'message': 'Company ID is required.'})

        try:
            company = CompanyProfile.objects.get(id=company_id)
        except CompanyProfile.DoesNotExist:
            return Response({'status': 'no', 'message': 'Company not found.'})

        candidate = None
        if lid:
            try:
                candidate = CandidateProfile.objects.get(user__id=lid)
            except CandidateProfile.DoesNotExist:
                pass

        try:
            rating = float(rating_str)
            rating = max(1.0, min(5.0, rating))
        except (ValueError, TypeError):
            rating = 5.0

        CompanyReview.objects.create(
            company=company,
            candidate=candidate,
            rating=rating,
            review=review_text
        )

        return Response({
            'status': 'success',
            'message': 'Review submitted successfully!'
        })


@extend_schema(tags=['Flutter Compatibility'])
class LegacyUserViewVacancyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        vacancies = Vacancy.objects.filter(
            status=Vacancy.Status.ACTIVE,
            company__verification_status=CompanyProfile.VerificationStatus.APPROVED,
            application_deadline__gte=timezone.localdate()
        ).select_related('company').order_by('-start_date')

        data = []
        for v in vacancies:
            data.append({
                'id': str(v.id),
                'position': v.position,
                'no_of_vaccancy': str(v.no_of_vacancy),
                'start': str(v.start_date),
                'end': str(v.application_deadline),
                'COMPANY': v.company.company_name
            })

        return Response({
            'status': 'ok',
            'data': data
        })


@extend_schema(tags=['Flutter Compatibility'])
class LegacyUserApplyVacancyView(APIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, *args, **kwargs):
        lid = request.data.get('lid')
        vacancy_id = request.data.get('id') or request.data.get('vacancy_id')

        if not lid or not vacancy_id:
            return Response({'status': 'no', 'message': 'User ID (lid) and Vacancy ID are required.'})

        try:
            candidate = CandidateProfile.objects.get(user__id=lid)
        except CandidateProfile.DoesNotExist:
            return Response({'status': 'no', 'message': 'Candidate profile not found.'})

        try:
            vacancy = Vacancy.objects.get(id=vacancy_id)
        except Vacancy.DoesNotExist:
            return Response({'status': 'no', 'message': 'Vacancy not found.'})

        if vacancy.status != Vacancy.Status.ACTIVE or vacancy.application_deadline < timezone.localdate():
            return Response({'status': 'no', 'message': 'This vacancy is no longer accepting applications.'})

        if Application.objects.filter(vacancy=vacancy, candidate=candidate).exists():
            return Response({
                'status': 'no',
                'message': 'You have already applied for this vacancy.'
            })

        app = Application.objects.create(
            vacancy=vacancy,
            candidate=candidate,
            status=Application.Status.PENDING
        )

        if 'resume' in request.FILES:
            app.resume = request.FILES['resume']
            app.save()

        return Response({
            'status': 'ok',
            'message': 'Applied successfully'
        })


@extend_schema(tags=['Flutter Compatibility'])
class LegacyViewAppliedVacancyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        lid = request.data.get('lid')
        if not lid:
            return Response({'status': 'no', 'message': 'User ID (lid) required.'})

        try:
            candidate = CandidateProfile.objects.get(user__id=lid)
        except CandidateProfile.DoesNotExist:
            return Response({'status': 'no', 'message': 'Candidate profile not found.'})

        applications = Application.objects.filter(candidate=candidate).select_related('vacancy__company').order_by('-applied_at')

        data = []
        for app in applications:
            status_display = app.status.capitalize()
            data.append({
                'id': str(app.id),
                'VACCANCY': app.vacancy.position,
                'company': app.vacancy.company.company_name,
                'status': status_display,
                'date': str(app.applied_at.date()),
                'start': 'N/A',
                'end': 'N/A'
            })

        return Response({
            'status': 'ok',
            'data': data
        })


@extend_schema(tags=['Flutter Compatibility'])
class LegacyUserViewTestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        candidate_param = request.data.get('candidate_id')
        if not candidate_param:
            return Response({'status': 'no', 'message': 'candidate_id parameter required.'})

        candidate = None
        vacancy = None

        if Application.objects.filter(id=candidate_param).exists():
            app = Application.objects.get(id=candidate_param)
            candidate = app.candidate
            vacancy = app.vacancy
        elif CandidateProfile.objects.filter(id=candidate_param).exists():
            candidate = CandidateProfile.objects.get(id=candidate_param)
        elif CandidateProfile.objects.filter(user__id=candidate_param).exists():
            candidate = CandidateProfile.objects.get(user__id=candidate_param)

        if not candidate:
            return Response({'status': 'no', 'message': 'Candidate or application not found.'})

        assignments = TestCandidateAssignment.objects.filter(candidate=candidate).select_related('test')
        if vacancy and vacancy.company:
            company_assignments = assignments.filter(test__company=vacancy.company)
            if company_assignments.exists():
                assignments = company_assignments

        if not assignments.exists():
            return Response({
                'status': 'no',
                'message': 'No tests currently scheduled for this candidate.'
            })

        data = []
        for assign in assignments:
            test = assign.test
            start_str = test.start_time.strftime("%I:%M %p") if test.start_time else "N/A"
            end_str = test.end_time.strftime("%I:%M %p") if test.end_time else "N/A"
            data.append({
                'test_name': test.test_name,
                'test_type': test.test_type,
                'date': str(test.date),
                'start': start_str,
                'end': end_str,
                'status': test.status.capitalize()
            })

        return Response({
            'status': 'ok',
            'data': data
        })


@extend_schema(tags=['Flutter Compatibility'])
class LegacySendFeedbackView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        feedback_text = request.data.get('feedback', '').strip()
        lid = request.data.get('lid')

        if not feedback_text:
            return Response({'status': 'no', 'message': 'Feedback text cannot be empty.'})

        user = None
        if lid:
            user = User.objects.filter(id=lid).first()
        if not user:
            user = User.objects.filter(role=User.Role.CANDIDATE).first() or User.objects.first()

        Feedback.objects.create(
            user=user,
            feedback_text=feedback_text
        )

        return Response({
            'status': 'ok',
            'message': 'Feedback submitted successfully'
        })


@extend_schema(tags=['Flutter Compatibility'])
class LegacySendComplaintView(APIView):
    permission_classes = [permissions.AllowAny]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request, *args, **kwargs):
        complaint_text = request.data.get('complaint', '').strip()
        lid = request.data.get('lid')
        company_param = request.data.get('company')

        if not complaint_text:
            return Response({'status': 'no', 'message': 'Complaint description cannot be empty.'})

        user = None
        if lid:
            user = User.objects.filter(id=lid).first()
        if not user:
            user = User.objects.filter(role=User.Role.CANDIDATE).first() or User.objects.first()

        company = None
        if company_param:
            if str(company_param).isdigit():
                company = CompanyProfile.objects.filter(id=company_param).first()
            if not company:
                company = CompanyProfile.objects.filter(company_name__iexact=str(company_param)).first()

        Complaint.objects.create(
            user=user,
            company=company,
            complaint_text=complaint_text,
            status=Complaint.Status.PENDING
        )

        return Response({
            'status': 'ok',
            'message': 'Complaint submitted successfully'
        })


@extend_schema(tags=['Flutter Compatibility'])
class LegacyUserViewReplyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        lid = request.data.get('lid')
        if not lid:
            return Response({'status': 'no', 'message': 'lid is required.'})

        complaints = Complaint.objects.filter(user__id=lid).order_by('-created_at')

        complaint_list = []
        for c in complaints:
            reply_text = c.reply if c.reply else "Pending Admin Reply"
            complaint_list.append({
                'id': str(c.id),
                'complaint': c.complaint_text,
                'reply': reply_text,
                'replay': reply_text,
                'date': c.created_at.strftime('%Y-%m-%d'),
                'status': c.status.capitalize(),
                'company': c.company.company_name if c.company else "General Platform"
            })

        return Response({
            'status': 'ok',
            'key': complaint_list,
            'data': complaint_list
        })
