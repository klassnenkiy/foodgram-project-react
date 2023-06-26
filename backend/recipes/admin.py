from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field
from .models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                     ShoppingCart, Tag)


class IngredientsResource(resources.ModelResource):
    name = Field(
        column_name='name',
        attribute='name',
    )
    measurement_unit = Field(
        column_name='measurement_unit',
        attribute='measurement_unit',
    )
    id = Field(
        attribute='id',
        column_name='id'
    )

    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit'
        )


@admin.register(Ingredient)
class IngredientAdmin(ImportExportModelAdmin):
    resource_class = IngredientsResource
    list_display = (
        'id',
        'name',
        'measurement_unit',
    )
    list_filter = ('name',)


class RecipeIngredientInline(admin.TabularInline):
    model = IngredientInRecipe
    min_num = 1


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
class TagAdmin(ImportExportModelAdmin):
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
