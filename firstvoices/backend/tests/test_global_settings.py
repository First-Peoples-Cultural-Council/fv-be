import re

import pytest

from firstvoices.settings import CORS_ALLOWED_ORIGIN_REGEXES


class TestCORSBaseRegex:
    CORS_BASE_REGEX = CORS_ALLOWED_ORIGIN_REGEXES[0]

    @pytest.mark.parametrize(
        "input_domain",
        [
            "http://localhost:3000",
            "https://localhost:3000",
            "https://abc.localhost:3000",
            "https://abc-def.localhost:3000",
        ],
    )
    def test_valid_domains(self, input_domain):
        matches = re.match(self.CORS_BASE_REGEX, input_domain)
        assert matches is not None
        assert input_domain in matches.string

    @pytest.mark.parametrize(
        "input_domain",
        [
            "http://invalid-domain.com",
            "https://also-not-valid-localhost:3000",
        ],
    )
    def test_invalid_domains(self, input_domain):
        matches = re.match(self.CORS_BASE_REGEX, input_domain)
        assert matches is None
