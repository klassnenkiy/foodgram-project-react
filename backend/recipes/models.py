from django.conf import settings
from django.db import models
from users.models import User


class Tag(models.Model):
    name = models.CharField(
        verbose_name='Тег',
        max_length=200,
        unique=True,
    )
    slug = models.CharField(
        verbose_name='Слаг',
        max_length=200,
        unique=True
    )
    color = models.CharField(
        verbose_name='Цвет',
        max_length=7,
        default='#E26C2D',
        unique=True,
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='Название',
        max_length=200,
    )
    measurement_unit = models.CharField(
        verbose_name='Единицы измерения',
        max_length=200,
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='recipe',
    )
    name = models.CharField(
        verbose_name='Название',
        max_length=200,
    )
    image = models.ImageField(
        upload_to='recipes/images/',
        null=True,
        default=None,
        verbose_name='Фотография блюда'
    )
    text = models.TextField(
        verbose_name='Описание',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        default=1,
        blank=False,
        verbose_name='Время приготовления (в минутах)',
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = [
            models.UniqueConstraint(fields=['author', 'name'],
                                    name='unique_author_recipename'
        )
        ]

    def __str__(self):
        return self.name


class IngredientInRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='+'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name='Рецепт'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество в рецепте',
    )

    def __str__(self):
        return self.recipe.name

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецепте'


class Favorite(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='+',
    )
    recipe_lover = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='Добавил в избранное',
        related_name='favorite',
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'


class ShoppingCart(models.Model):
    cart_owner = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='Владелец списка покупок',
        related_name='shopping_cart',
    )
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='+',
    )

    def __str__(self):
        return self.recipe.name

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'