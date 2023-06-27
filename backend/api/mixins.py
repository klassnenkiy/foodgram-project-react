from rest_framework import mixins, status, viewsets
from rest_framework.response import Response


class CreateDestroyViewSet(mixins.CreateModelMixin,
                           mixins.DestroyModelMixin,
                           viewsets.GenericViewSet):
    pass


class DeleteActionMixin:
    def delete_action(self, request, recipe_id):
        recipe = self.kwargs.get('recipe_id')
        owner = self.request.user

        queryset = self.queryset.filter(recipe=recipe, owner=owner)
        if not queryset.exists():
            return Response({'errors': self.error_message},
                            status=status.HTTP_400_BAD_REQUEST)

        queryset.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
