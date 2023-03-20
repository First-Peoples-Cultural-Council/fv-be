from django.contrib.auth.models import AbstractBaseUser, Group, Permission
from django.db import models

from .Role import Role


class User(AbstractBaseUser):
	"""
	User Model
	"""
	USERNAME_FIELD = 'id'
	REQUIRED_FIELDS = []

	"""
	Maps to JWT 'sub' field -- this is the primary key
	"""
	id = models.CharField(
		max_length=64,
		blank=False,
		unique=True,
		primary_key=True,
		null=False
	)

	@property
	def password(self):
		return None

	@property
	def is_staff(self):
		return None

	@property
	def is_active(self):
		return True

	@property
	def is_superuser(self):
		return False

	@property
	def is_anonymous(self):
		return False

	@property
	def username(self):
		return self.sub

	@property
	def is_authenticated(self):
		return True

	"""
	@todo decide how to store group information -- this is here to erase the default from the base class
	"""

	@property
	def groups(self):
		return None

	@property
	def user_permissions(self):
		return None

	def set_password(self, raw_password):
		raise NotImplementedError(
			"Nonsensical operation"
		)

	def check_password(self, raw_password):
		raise NotImplementedError(
			"Nonsensical operation"
		)

	def __str__(self):
		return str(self.id)

	def natural_key(self):
		return self.id,

	@property
	def roles(self):
		"""
		Roles
		"""
		return Role.objects.filter(user_roles__user_id=self.id)

	class Meta:
		db_table = 'user'
