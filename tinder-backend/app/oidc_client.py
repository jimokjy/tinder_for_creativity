"""
Регистрация OIDC-клиента для входа через ЛК Силаэдра (authlib).

Адрес provider'а (issuer) публикует стандартный discovery-документ по
`{issuer}/.well-known/openid-configuration` — authlib сам находит через
него authorization_endpoint, token_endpoint, jwks_uri и т.д., вручную
прописывать их не нужно.
"""
from authlib.integrations.starlette_client import OAuth

from app.config import (
    CRM_OIDC_ENABLED,
    CRM_OIDC_ISSUER,
    CRM_OIDC_CLIENT_ID,
    CRM_OIDC_CLIENT_SECRET,
)

oauth = OAuth()

if CRM_OIDC_ENABLED:
    oauth.register(
        name="silaeder",
        client_id=CRM_OIDC_CLIENT_ID,
        client_secret=CRM_OIDC_CLIENT_SECRET,
        server_metadata_url=f"{CRM_OIDC_ISSUER.rstrip('/')}/.well-known/openid-configuration",
        client_kwargs={
            "scope": "openid profile email roles",
            # ЛК Силаэдра требует PKCE — без этого он отвечает
            # "Некорректный или отсутствующий PKCE code_challenge".
            # authlib сам генерирует code_verifier/code_challenge и хранит
            # verifier в сессии между redirect'ом на Силаэдр и callback'ом.
            "code_challenge_method": "S256",
        },
    )
