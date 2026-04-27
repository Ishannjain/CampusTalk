from django.http import JsonResponse
import logging

logger = logging.getLogger(__name__)

class GlobalErrorMiddleware:
    """
    Centralized error handling system.
    Returns standard error response format for API requests.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            logger.error(f"Unhandled Exception: {str(e)}", exc_info=True)
            return self.process_exception(request, e)

    def process_exception(self, request, exception):
        # Determine if it's an API request or expects JSON
        if request.path.startswith('/api/') or request.headers.get('Accept') == 'application/json':
            status_code = 500
            # You can add more specific exception handling here (e.g., PermissionDenied -> 403)
            
            return JsonResponse({
                "success": False,
                "message": str(exception),
                "code": exception.__class__.__name__.upper(),
                "details": {
                    "path": request.path,
                    "method": request.method
                }
            }, status=status_code)
        
        # For non-API requests, let Django's default handler (or custom error views) take over
        return None
