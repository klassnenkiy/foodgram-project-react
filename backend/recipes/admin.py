from django.contrib import admin
from .models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                     ShoppingCart, Tag)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'measurement_unit',
    )
    list_filter = ('name',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (RecipeIngredientInline,)
    list_display = (
        'id',
        'name',
        'author'
    )
    list_filter = (
        'name',
        'author',
        'tags',
    )


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'slug',
        'color',
    )
    list_filter = ('name',)


@admin.register(Favorite)
class Favorite(admin.ModelAdmin):
    list_display = (
        'recipe',
        'recipe_lover',
    )
    list_filter = ('recipe_lover',)


@admin.register(ShoppingCart)
class ShoppingCart(admin.ModelAdmin):
    list_display = (
        'cart_owner',
        'recipe',
    )
    list_filter = ('cart_owner',)
