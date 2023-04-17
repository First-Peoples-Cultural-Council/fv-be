from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
	def create_user(self, id, email, password=None):
		"""
		Creates and saves a User with the given email and sub
		"""
		if not email:
			raise ValueError("Users must have an email address")

		user = self.model(
			id=id,
			email=email
		)

		user.set_password(password)
		user.save(using=self._db)

		return user

	def create_superuser(self, id, email, password):
		"""
		Creates and saves a superuser with the given email and password
		"""
		if not email:
			raise ValueError("Admins must have password")

		user = self.create_user(
			id=email,
			email=email,
			password=password
		)

		user.is_superuser = True
		user.is_staff = True

		user.save(using=self._db)
		return user
