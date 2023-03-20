from django.db import models
from django.db.models import Model


class UserRole(Model):
	"""
	Join table for users to roles
	"""
	user = models.ForeignKey(
		'User',
		related_name='user_roles',
		on_delete=models.CASCADE
	)
	role = models.ForeignKey(
		'Role',
		related_name='user_roles',
		on_delete=models.CASCADE
	)

	class Meta:
		db_table = 'user_role'
