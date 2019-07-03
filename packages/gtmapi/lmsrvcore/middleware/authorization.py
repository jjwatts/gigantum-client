from lmsrvcore.auth.identity import get_identity_manager_instance, AuthenticationError, parse_token
import flask


class AuthorizationMiddleware(object):
    """Middleware to enforce authentication requirements and parse JWT"""
    identity_mgr = None

    def resolve(self, next, root, info, **args):
        if not self.identity_mgr:
            self.identity_mgr = get_identity_manager_instance()

        # On first field processed in request, authenticate
        if not hasattr(info.context, "auth_middleware_complete"):
            # Pull the token out of the header if available
            token = None
            if "Authorization" in info.context.headers:
                token = parse_token(info.context.headers["Authorization"])

            # Save token to the request context for future use (e.g. look up a user's profile information if needed)
            flask.g.access_token = token
            flask.g.id_token = info.context.headers.get("Identity", None)

            # Check if you are authenticated
            try:
                self.identity_mgr.is_authenticated(token, flask.g.id_token)
            except AuthenticationError:
                raise AuthenticationError("User not authenticated", 401)

            info.context.auth_middleware_complete = True

        return next(root, info, **args)
