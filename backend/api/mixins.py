from rest_framework import mixins, viewsets


class CreateDestroyViewSet(mixins.CreateModelMixin,
                           mixins.DestroyModelMixin,
                           viewsets.GenericViewSet):
    pass


class DeleteActionMixin:
    def delete(self, request, recipe_id):
        recipe = self.kwargs.get('recipe_id')
        owner = self.request.user

        if not self.queryset.filter(recipe=recipe, owner=owner).exists():
            return Response({'errors': self.error_message},
                            status=status.HTTP_400_BAD_REQUEST)

        self.queryset.filter(recipe=recipe, owner=owner).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)