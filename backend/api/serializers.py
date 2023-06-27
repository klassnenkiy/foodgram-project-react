import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.validators import ValidationError

from recipes.models import (Favorite, Ingredient, IngredientInRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import Subscribe, User


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


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


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = (
            'recipe',
            'recipe_lover'
        )
        read_only_fields = (
            'recipe',
            'recipe_lover'
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
        return Subscribe.objects.filter(
            user=user,
            author=obj
        ).exists()


class UserRegisterSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )

    def create(self, validated_data):
        user = User(
            email=validated_data['email'],
            username=validated_data['username'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


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
        fields = ('id', 'name', 'measurement_unit', 'amount')


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
            'image', 'text', 'cooking_time')

    def get_is_favorited(self, obj):
        return Favorite.objects.filter(
            recipe=obj, recipe_lover=self.context['request'].user).exists()

    def get_is_in_shopping_cart(self, obj):
        return ShoppingCart.objects.filter(
            recipe=obj, cart_owner=self.context['request'].user).exists()

    def get_ingredients(self, obj):
        queryset = IngredientInRecipe.objects.filter(recipe=obj)
        return IngredientInRecipeSerializer(queryset, many=True).data

    def validate(self, data):
        self.validate_tags(data)
        self.validate_ingredients(data)
        self.validate_cooking_time(data)
        return data

    def validate_tags(self, data):
        tags = self.initial_data.get('tags')
        if not tags:
            raise serializers.ValidationError({
                'tags': 'Кажется вы забыли указать тэги'})

        for tag in tags:
            if not Tag.objects.filter(pk=tag).exists():
                raise ValidationError(f'{tag} - Такого тэга не существует')

    def validate_ingredients(self, data):
        ingredients = self.initial_data.get('ingredients')
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

    def create(self, validated_data):
        tags = self.initial_data.get('tags')
        ingredients = self.initial_data.get('ingredients')
        new_recipe = Recipe.objects.create(
            **validated_data, author=self.context.get('request').user)
        new_recipe.tags.add(*tags)

        for ingredient in ingredients:
            ingredient_object = get_object_or_404(
                Ingredient, id=ingredient.get('id'))
            IngredientInRecipe.objects.create(
                recipe=new_recipe,
                ingredient=ingredient_object,
                amount=ingredient.get('amount'))
        return new_recipe

    def update(self, instance, validated_data):
        new_tags = self.initial_data.get('tags')
        new_ingredients = self.initial_data.get('ingredients')
        IngredientInRecipe.objects.filter(recipe=instance).delete()

        for tag in new_tags:
            if not Tag.objects.filter(pk=tag).exists():
                raise ValidationError(f'{tag} - Такого тэга не существует')

        if len(new_ingredients) < 1:
            raise ValidationError(
                'Блюдо должно содержать хотя бы 1 ингредиент')
        unique_list = []
        for ingredient in new_ingredients:
            if not ingredient.get('id'):
                raise ValidationError('Укажите id ингредиента')
            ingredient_id = ingredient.get('id')
            if not Ingredient.objects.filter(pk=ingredient_id).exists():
                raise ValidationError(
                    f'{ingredient_id}- ингредиент с таким id не найден')
            if id in unique_list:
                raise ValidationError(
                    f'{ingredient_id}- дублирующийся ингредиент')
            unique_list.append(id)
            ingredient_amount = ingredient.get('amount')
            if ingredient_amount < 1:
                raise ValidationError(
                    f'Количество {ingredient} должно быть больше 1')

        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time', instance.cooking_time)
        instance.save()
        for ingredient in new_ingredients:
            ingredient_object = get_object_or_404(
                Ingredient, id=ingredient.get('id'))
            IngredientInRecipe.objects.create(
                recipe=instance,
                ingredient=ingredient_object,
                amount=ingredient.get('amount'))
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
        requset = self.context.get('request')
        return RecipeToRepresentationSerializer(
            instance.recipe,
            context={'request': requset}
        ).data
