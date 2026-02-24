from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class OfficerManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Officers must have a username")
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)


class Officer(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = OfficerManager()

    USERNAME_FIELD = 'username'

    def __str__(self):
        return self.username


class Voter(models.Model):
    voter_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    fingerprint_template = models.TextField()

    def __str__(self):
        return self.voter_id


class Candidate(models.Model):
    name = models.CharField(max_length=100)
    symbol = models.ImageField(upload_to='candidate_symbols/')

    def __str__(self):
        return f"{self.name}"

class Vote(models.Model):
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE)
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.voter.voter_id} → {self.candidate.name}"
