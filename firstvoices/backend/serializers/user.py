from rest_framework import serializers


class CurrentUserSerializer(serializers.BaseSerializer):
	def to_representation(self, instance):
		return {
			'msg': 'if you are seeing this, you made an authenticated request successfully',
			'authenticated_id': instance.id,
		}
