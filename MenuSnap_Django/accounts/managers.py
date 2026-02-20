from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, name=None):
        if not email:
            raise ValueError("Email required")

        email = self.normalize_email(email)
        user = self.model(email=email, name=name)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, name="admin"):
        user = self.create_user(email=email, password=password, name=name)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user
