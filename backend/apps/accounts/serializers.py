from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from apps.candidates.models import CandidateProfile
from apps.companies.models import CompanyProfile

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Enhanced JWT token serializer returning role, username, email, and user ID.
    Supports login via email or username.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Allow client to submit either 'email' or 'username'
        self.fields['username'] = serializers.CharField(required=False)
        if self.username_field in self.fields:
            self.fields[self.username_field].required = False

    def validate(self, attrs):
        username_or_email = attrs.get(self.username_field) or attrs.get('username')
        if not username_or_email:
            raise serializers.ValidationError({self.username_field: "Email or username is required."})

        # Put the credential in the username field so SimpleJWT authenticate works
        attrs[self.username_field] = username_or_email.strip()

        data = super().validate(attrs)
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'username': self.user.username,
            'role': self.user.role,
            'is_active': self.user.is_active,
        }

        # Include profile status
        if self.user.role == User.Role.COMPANY:
            profile = getattr(self.user, 'company_profile', None)
            data['user']['verification_status'] = profile.verification_status if profile else 'PENDING'
            data['user']['company_name'] = profile.company_name if profile else ''
        elif self.user.role == User.Role.CANDIDATE:
            profile = getattr(self.user, 'candidate_profile', None)
            data['user']['full_name'] = profile.full_name if profile else ''

        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'role', 'created_at', 'updated_at']


class CandidateRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    full_name = serializers.CharField(max_length=255, required=True)
    phone = serializers.CharField(max_length=50, required=False, allow_blank=True)
    place = serializers.CharField(max_length=150, required=False, allow_blank=True)
    dob = serializers.DateField(required=False, allow_null=True)
    gender = serializers.CharField(max_length=20, required=False, allow_blank=True)
    city = serializers.CharField(max_length=150, required=False, allow_blank=True)
    state = serializers.CharField(max_length=150, required=False, allow_blank=True)
    post = serializers.CharField(max_length=150, required=False, allow_blank=True)
    pin = serializers.CharField(max_length=20, required=False, allow_blank=True)
    photo = serializers.ImageField(required=False, allow_null=True)
    resume = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'password', 'confirm_password',
            'full_name', 'phone', 'place', 'dob', 'gender',
            'city', 'state', 'post', 'pin', 'photo', 'resume'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        full_name = validated_data.pop('full_name')
        phone = validated_data.pop('phone', '')
        place = validated_data.pop('place', '')
        dob = validated_data.pop('dob', None)
        gender = validated_data.pop('gender', '')
        city = validated_data.pop('city', '')
        state = validated_data.pop('state', '')
        post = validated_data.pop('post', '')
        pin = validated_data.pop('pin', '')
        photo = validated_data.pop('photo', None)
        resume = validated_data.pop('resume', None)

        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data.get('username') or validated_data['email'].split('@')[0],
            password=validated_data['password'],
            role=User.Role.CANDIDATE
        )

        CandidateProfile.objects.create(
            user=user,
            full_name=full_name,
            phone=phone,
            place=place,
            dob=dob,
            gender=gender,
            city=city,
            state=state,
            post=post,
            pin=pin,
            photo=photo,
            resume=resume
        )
        return user


class CompanyRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    company_name = serializers.CharField(max_length=255, required=True)
    phone = serializers.CharField(max_length=50, required=True)
    address = serializers.CharField(required=True)
    website = serializers.URLField(max_length=255, required=False, allow_blank=True)
    description = serializers.CharField(required=False, allow_blank=True)
    logo = serializers.ImageField(required=False, allow_null=True)
    registration_document = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'password', 'confirm_password',
            'company_name', 'phone', 'address', 'website',
            'description', 'logo', 'registration_document'
        ]

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        company_name = validated_data.pop('company_name')
        phone = validated_data.pop('phone')
        address = validated_data.pop('address')
        website = validated_data.pop('website', '')
        description = validated_data.pop('description', '')
        logo = validated_data.pop('logo', None)
        registration_document = validated_data.pop('registration_document', None)

        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data.get('username') or validated_data['email'].split('@')[0],
            password=validated_data['password'],
            role=User.Role.COMPANY,
            is_active=True
        )

        CompanyProfile.objects.create(
            user=user,
            company_name=company_name,
            email=validated_data['email'],
            phone=phone,
            address=address,
            website=website,
            description=description,
            logo=logo,
            registration_document=registration_document,
            verification_status=CompanyProfile.VerificationStatus.PENDING
        )
        return user


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "New passwords do not match."})
        return attrs
