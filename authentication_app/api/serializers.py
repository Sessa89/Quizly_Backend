'''Serializers for authentication-related APIs.

Currently exposes:
- RegistrationSerializer: validates and creates a new Django User.

Notes:
- Username and email must be unique (validated via DRF UniqueValidator).
- Password is validated against Django's AUTH_PASSWORD_VALIDATORS and must be
  at least 6 characters (frontend requirement).
- Password is write-only; it is never returned in responses.
'''

from typing import Dict
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

class RegistrationSerializer(serializers.ModelSerializer):
    '''Validate input and create a new user account.

    Fields:
        username (str): Required, unique; max length 150.
        email (str): Required, valid email, unique.
        password (str): Required, write-only; min length 6; validated by Django's
            password validators (AUTH_PASSWORD_VALIDATORS).

    Validation:
        - Enforces unique username and email.
        - Runs Django's password validation (common/length/numeric/etc.).
          Any violations raise serializers.ValidationError.

    Create behavior:
        - Uses `User.objects.create_user(...)` to ensure the password
          is properly hashed.
    '''

    username = serializers.CharField(
        max_length=150,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message='This username is already taken.'
            )
        ]
    )
    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="This email is already taken."
            )
        ]
    )
    password = serializers.CharField(write_only=True, min_length=6)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def validate_password(self, value: str) -> str:
        '''Run Django's configured password validators on the provided value.

        Args:
            value: The raw password string.

        Returns:
            The same password value if validation succeeds.

        Raises:
            serializers.ValidationError: If any password validator fails.
        '''

        validate_password(value)
        return value

    def create(self, validated_data: Dict) -> User:
        '''Create a new user with a hashed password.

        Args:
            validated_data: Serializer-validated data for the new user.

        Returns:
            The created `User` instance.
        '''
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )

        return user