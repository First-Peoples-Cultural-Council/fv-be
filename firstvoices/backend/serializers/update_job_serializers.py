from backend.serializers.import_job_serializers import ImportJobSerializer


class UpdateJobSerializer(ImportJobSerializer):
    def build_url_field(self, field_name, model_class):
        """
        Add our namespace to the view_name
        """
        field_class, field_kwargs = super().build_url_field(field_name, model_class)
        field_kwargs["view_name"] = "api:updatejob-detail"

        return field_class, field_kwargs
