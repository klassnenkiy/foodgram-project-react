from django_filters.rest_framework import FilterSet, filters
from rest_framework.filters import SearchFilter

from recipes.models import Favorite, Recipe, ShoppingCart


class RecipeFilter(FilterSet):
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        reс_pk = Favorite.objects.filter(
            recipe_lover=self.request.user).values('recipe_id')
        if value:
            return queryset.filter(pk__in=reс_pk)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        reс_pk = ShoppingCart.objects.filter(
            cart_owner=self.request.user).values('recipe_id')
        if value:
            return queryset.filter(pk__in=reс_pk)
        return queryset


class IngredientSearchFilter(SearchFilter):
    search_param = 'name'
