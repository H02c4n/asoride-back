from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken


@database_sync_to_async
def get_user_from_token(token: str):
    try:
        access = AccessToken(token)
        user_id = access['user_id']
        from apps.users.models import User
        user = User.objects.get(id=user_id)
        print(f"[WS-MW] JWT OK: user={user.username} id={user.id}")
        return user
    except Exception as e:
        print(f"[WS-MW] JWT HATA: {type(e).__name__}: {e}")
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        params = parse_qs(query_string)
        token = params.get('token', [None])[0]

        if token:
            print(f"[WS-MW] Token geldi (ilk 30): {token[:30]}...")
            scope['user'] = await get_user_from_token(token)
        else:
            print("[WS-MW] Token YOK")
            scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)