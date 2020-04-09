from django.db import models


class Profile(models.Model):
    external_id = models.PositiveIntegerField(
        unique=True,
    )
    name = models.TextField()

    def __str__(self):
        return f'#{self.external_id} {self.name}'


class Message(models.Model):
    profile = models.ForeignKey(
        to='Profile',
        on_delete=models.PROTECT,
    )
    text = models.TextField()
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    def __str__(self):
        return f'Message {self.pk} from {self.profile}'


class Order(models.Model):
    profile = models.ForeignKey(
        to='Profile',
        on_delete=models.PROTECT,
    )
    date = models.DateTimeField(
        auto_now_add=True,
    )
    subject = models.TextField()
    deadline = models.TextField()
    description = models.TextField()
    status = models.TextField()  # new, paid, canceled, done
    chat = models.IntegerField()
    price = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f'{self.pk} from {self.profile}'


class FreelanceApplication(models.Model):
    profile = models.ForeignKey(
        to='Profile',
        on_delete=models.PROTECT,
    )
    date = models.DateTimeField(
        auto_now_add=True,
    )
    description = models.TextField()

    def __str__(self):
        return f'{self.pk} from {self.profile}'
