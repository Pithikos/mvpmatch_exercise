from rest_framework import routers
from api.views import UserViewSet, ProductViewSet

router = routers.SimpleRouter()
router.register(r'users', UserViewSet)
router.register(r'products', ProductViewSet)


urlpatterns = router.urls
