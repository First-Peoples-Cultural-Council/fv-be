from rest_framework import serializers


class CurrentUserSerializer(serializers.BaseSerializer):
	def to_representation(self, instance):
		return {
			'hello': 'world'
		}
