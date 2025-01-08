from backend.models.base import SanitizedHtmlField


class TestSanitizedHtmlField:
    field = SanitizedHtmlField()

    def test_field_empty(self):
        result = self.field.to_python("")
        assert result == ""

    def test_field_allowed_html(self):
        result = self.field.to_python("<p>Hello World</p>")
        assert result == "<p>Hello World</p>"

    def test_field_cleans_html(self):
        result = self.field.to_python(
            "<script src=example.com/malicious.js></script><strong>Arm</strong>"
        )
        assert result == "<strong>Arm</strong>"

        result = self.field.to_python("<script>alert('XSS');</script>")
        assert result == ""

    def test_field_no_html(self):
        result = self.field.to_python("The French person said << quoi ?? >>")
        assert result == "The French person said << quoi ?? >>"

        result = self.field.to_python("Why is 1 < 2 ?")
        assert result == "Why is 1 < 2 ?"
