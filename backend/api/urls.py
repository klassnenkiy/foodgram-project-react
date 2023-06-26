from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api import views

app_name = 'api'

router = DefaultRouter()
router.register('recipes', views.RecipeViewSet, basename='recipes')
router.register(
    r'recipes/(?P<recipe_id>\d+)/favorite',
    views.FavoriteViewSet, basename='favorite')
router.register(
    'users/subscriptions',
    views.SubscriptionsViewSet, basename='subscriptions')
router.register('tags', views.TagViewSet, basename='tags')
router.register('ingredients', views.IngredientViewSet, basename='ingredients')
router.register(
    r'recipes/(?P<recipe_id>\d+)/shopping_cart',
    views.ShoppingCartViewSet, basename='shopping_cart')


urlpatterns = [
    path(
        'recipes/download_shopping_cart/',
        views.DownloadShoppingCart.as_view()),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('users/<int:author_id>/subscribe/', views.SubscribeAPIView.as_view())
    ]
