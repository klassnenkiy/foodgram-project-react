from django.db.models import Sum
from django.shortcuts import HttpResponse, get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import exceptions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscribe, User
from .filters import IngredientSearchFilter, RecipeFilter
from .mixins import CreateDestroyViewSet
from .paginators import PageLimitPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (FavoriteRecipeSerializer, IngredientSerializer,
                          RecipeSerializer, ShoppingCartSerializer,
                          SubscribeSerializer, TagSerializer)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    pagination_class = PageLimitPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    serializer_class = RecipeSerializer
    permission_classes = (IsAuthorOrReadOnly,)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name',)


class SubscriptionsViewSet(viewsets.ModelViewSet):
    serializer_class = SubscribeSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = PageLimitPagination

    def get_queryset(self):
        return Subscribe.objects.filter(
            user=self.request.user).prefetch_related('author')


class SubscribeAPIView(APIView):
    def post(self, request, author_id):
        author = get_object_or_404(
            User,
            id=author_id
        )
        if request.user == author:
            return Response(
                {'errors': 'Нельзя подписаться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription = Subscribe.objects.filter(
            author=author,
            user=request.user,
        )
        if subscription.exists():
            return Response(
                {'errors': 'Вы уже подписаны на этого автора'},
                status=status.HTTP_400_BAD_REQUEST
            )
        queryset = Subscribe.objects.create(
            author=author,
            user=request.user,
        )
        serializer = SubscribeSerializer(
            queryset,
            context={'request': request}
        )
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )

    def delete(self, request, author_id):
        user = request.user
        author = get_object_or_404(
            User,
            id=author_id,
        )
        subscription = Subscribe.objects.filter(
            author=author,
            user=user,
        )
        if not subscription.exists():
            return Response(
                {'errors': 'Вы не подписаны на этого автора'},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AddRemoveFromListMixin:
    item_model = None
    item_field = None
    owner_field = None
    error_message_add = None
    error_message_remove = None

    def perform_action(self, request, recipe_id, error_message):
        item_model = self.item_model
        item_field = self.item_field
        owner_field = self.owner_field
        user = request.user
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        if item_model.objects.filter(
            **{item_field: recipe, owner_field: user}
        ).exists():
            raise exceptions.ValidationError(error_message)
        item_model.objects.create(
            **{item_field: recipe, owner_field: user}
        )
        return Response(status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=['POST'],
        permission_classes=[IsAuthenticated]
    )
    def add(self, request, pk=None):
        error_message = self.error_message_add
        return self.perform_action(request, pk, error_message)

    @action(
        detail=True,
        methods=['DELETE'],
        permission_classes=[IsAuthenticated]
    )
    def remove(self, request, pk=None):
        error_message = self.error_message_remove
        item_model = self.item_model
        item_field = self.item_field
        owner_field = self.owner_field
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if not item_model.objects.filter(
            **{item_field: recipe, owner_field: user}
        ).exists():
            return Response(
                {'errors': error_message},
                status=status.HTTP_400_BAD_REQUEST
            )
        item_model.objects.filter(
            **{item_field: recipe, owner_field: user}
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class FavoriteViewSet(AddRemoveFromListMixin, viewsets.ModelViewSet):
    queryset = Favorite.objects.all()
    serializer_class = FavoriteRecipeSerializer
    permission_classes = [IsAuthenticated]
    item_model = Favorite
    item_field = 'recipe'
    owner_field = 'user'
    error_message_add = 'Рецепт уже есть в избранном.'
    error_message_remove = 'Рецепта нет в избранном.'


class ShoppingCartViewSet(AddRemoveFromListMixin, CreateDestroyViewSet):
    queryset = ShoppingCart.objects.all()
    serializer_class = ShoppingCartSerializer
    permission_classes = [IsAuthenticated]
    item_model = ShoppingCart
    item_field = 'recipe'
    owner_field = 'user'
    error_message_add = 'Рецепт уже есть в списке покупок.'
    error_message_remove = 'Рецепта нет в списке покупок.'


class DownloadShoppingCart(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        if not ShoppingCart.objects.filter(user=request.user).exists():
            return Response({'errors': 'в списке покупок ничего нет'},
                            status=status.HTTP_400_BAD_REQUEST)
        rec_pk = ShoppingCart.objects.filter(
            user=request.user).values('recipe_id')
        ingredients = IngredientInRecipe.objects.filter(
            recipe_id__in=rec_pk).values(
                'ingredient__name', 'ingredient__measurement_unit').annotate(
                    total_amount=Sum('amount')).order_by()

        text = 'Список покупок:\n\n'
        for item in ingredients:
            text += (f'{item["ingredient__name"]}: '
                     f'{item["total_amount"]} '
                     f'{item["ingredient__measurement_unit"]}\n')

        response = HttpResponse(text, content_type='text/plain')
        filename = 'recipes_list.txt'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response


class DownloadShoppingCart(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        if not ShoppingCart.objects.filter(user=request.user).exists():
            return Response({'errors': 'в списке покупок ничего нет'},
                            status=status.HTTP_400_BAD_REQUEST)
        rec_pk = ShoppingCart.objects.filter(
            user=request.user).values('recipe_id')
        ingredients = IngredientInRecipe.objects.filter(
            recipe_id__in=rec_pk).values(
                'ingredient__name', 'ingredient__measurement_unit').annotate(
                    total_amount=Sum('amount')).order_by()

        text = 'Список покупок:\n\n'
        for item in ingredients:
            text += (f'{item["ingredient__name"]}: '
                     f'{item["total_amount"]} '
                     f'{item["ingredient__measurement_unit"]}\n')

        response = HttpResponse(text, content_type='text/plain')
        filename = 'recipes_list.txt'
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
