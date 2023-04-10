import os


def config():
	return {
		'JWKS_URL': os.getenv('JWT_JWKS_URL'),
		'AUDIENCE': os.getenv('JWT_JWKS_AUDIENCE')
	}
