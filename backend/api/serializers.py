from rest_framework import serializers
from rest_framework.validators import ValidationError

from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscribe, User
from .fields import Base64ImageField


class RecipeToRepresentationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'color',
            'slug'
        )


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='recipe.id')
    name = serializers.ReadOnlyField(source='recipe.name')
    image = serializers.CharField(source='recipe.image', read_only=True)
    cooking_time = serializers.ReadOnlyField(source='recipe.cooking_time')

    class Meta:
        model = Favorite
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )
        read_only_fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )

    def validate(self, data):
        user = self.context.get('request').user
        recipe = self.context.get('recipe')
        if Favorite.objects.filter(recipe_lover=user, recipe=recipe).exists():
            raise serializers.ValidationError({
                'errors': 'Рецепт уже в избранном'})
        return data


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit'
        )


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return user.follower.filter(author=obj).exists()


class SubscribeSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source='author.email')
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    is_subscrubed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscribe
        fields = (
            'email', 'id',
            'username', 'first_name',
            'last_name', 'is_subscrubed',
            'recipes', 'recipes_count'
        )

    def get_is_subscrubed(self, obj):
        """метод для просмотра текущих подписок всегда тру"""
        return True

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes = obj.author.recipe.all()
        recipes_limit = request.query_params.get('recipes_limit')
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        return RecipeToRepresentationSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return obj.author.recipe.count()


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(
        source='ingredient.id',
    )
    name = serializers.ReadOnlyField(
        source='ingredient.name',
    )
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit',
    )

    class Meta:
        model = IngredientInRecipe
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    ingredients = serializers.SerializerMethodField(read_only=True)
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)
    image = Base64ImageField(use_url=True, max_length=None)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author',
            'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name',
            'image', 'text', 'cooking_time',
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(
            recipe=obj, recipe_lover=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(
            recipe=obj, cart_owner=request.user).exists()

    def get_ingredients(self, obj):
        queryset = IngredientInRecipe.objects.filter(recipe=obj)
        return IngredientInRecipeSerializer(queryset, many=True).data

    def validate_tags(self, data):
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError({
                'tags': 'Кажется вы забыли указать тэги'})

        for tag in tags:
            if not Tag.objects.filter(pk=tag).exists():
                raise ValidationError(f'{tag} - Такого тэга не существует')

    def validate_ingredients(self, data):
        ingredients = data.get('ingredients')
        if len(ingredients) < 1:
            raise ValidationError(
                'Блюдо должно содержать хотя бы 1 ингредиент')
        unique_list = []
        for ingredient in ingredients:
            if not ingredient.get('id'):
                raise ValidationError('Укажите id ингредиента')
            ingredient_id = ingredient.get('id')
            if not Ingredient.objects.filter(pk=ingredient_id).exists():
                raise ValidationError(
                    f'{ingredient_id}- ингредиент с таким id не найден')
            if ingredient_id in unique_list:
                raise ValidationError(
                    f'{ingredient_id}- дублирующийся ингредиент')
            unique_list.append(ingredient_id)
            ingredient_amount = ingredient.get('amount')
            if ingredient_amount < 1:
                raise ValidationError(
                    f'Количество {ingredient} должно быть больше 1')

    def validate_cooking_time(self, data):
        cooking_time = data.get('cooking_time')
        if not cooking_time or int(cooking_time) <= 0:
            raise serializers.ValidationError({
                'cooking_time': 'Укажите время приготовления'})

    def create_or_update_ingredients(self, recipe, ingredients):
        IngredientInRecipe.objects.filter(recipe=recipe).delete()
        bulk_create_data = (
            IngredientInRecipe(
                recipe=recipe,
                ingredient=ingredient.get('id'),
                amount=ingredient.get('amount'))
            for ingredient in ingredients)
        IngredientInRecipe.objects.bulk_create(bulk_create_data)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipe')
        new_recipe = Recipe.objects.create(
            **validated_data, author=self.context.get('request').user)
        new_recipe.tags.add(*tags)
        self.create_or_update_ingredients(new_recipe, ingredients)
        return new_recipe

    def update(self, instance, validated_data):
        new_tags = validated_data.pop('tags')
        new_ingredients = validated_data.pop('ingredients')
        super().update(instance, validated_data)
        self.create_or_update_ingredients(instance, new_ingredients)
        instance.tags.clear()
        instance.tags.set(new_tags)
        return instance


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('cart_owner', 'recipe')
        read_only_fields = ('cart_owner', 'recipe')

    def validate(self, data):
        cart_owner = self.context.get('request').user
        recipe = self.context.get('recipe')
        data['recipe'] = recipe
        data['cart_owner'] = cart_owner
        if ShoppingCart.objects.filter(cart_owner=cart_owner,
                                       recipe=recipe).exists():
            raise serializers.ValidationError({
                'errors': 'Рецепт уже в списке покупок'})
        return data

    def to_representation(self, instance):
        request = self.context.get('request')
        return RecipeToRepresentationSerializer(
            instance.recipe,
            context={'request': request}
        ).data
