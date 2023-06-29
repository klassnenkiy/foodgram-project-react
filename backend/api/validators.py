from django.core.exceptions import ValidationError


def validate_ingredients(ingredients_list, val_model):
    if len(ingredients_list) < 1:
        raise ValidationError(
            'Блюдо должно содержать хотя бы 1 ингредиент')
    unique_list = []
    for ingredient in ingredients_list:
        if not ingredient.get('id'):
            raise ValidationError('Укажите id ингредиента')
        ingredient_id = ingredient.get('id')
        if not val_model.objects.filter(pk=ingredient_id).exists():
            raise ValidationError(
                f'{ingredient_id}- ингредиент с таким id не найден')
        if id in unique_list:
            raise ValidationError(
                f'{ingredient_id}- дублирующийся ингредиент')
        unique_list.append(ingredient_id)
        ingredient_amount = ingredient.get('amount')
        if int(ingredient_amount) < 1:
            raise ValidationError(
                f'Количество {ingredient} должно быть больше 1')


def validate_tags(tags_list, val_model):
    for tag in tags_list:
        if not val_model.objects.filter(pk=tag).exists():
            raise ValidationError(f'{tag} - Такого тэга не существует')


def validate_cooking_time(value):
    if not value or int(value) < 1:
        raise ValidationError({
            'cooking_time': 'Укажите время приготовления'})
