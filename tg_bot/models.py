from django.db import models


class Profile(models.Model):
    external_id = models.PositiveIntegerField(
        unique=True,
    )
    name = models.TextField(null=True, blank=True)
    card_number = models.TextField(null=True, blank=True)
    keywords = models.TextField(default='')
    balance = models.IntegerField(default=0)
    promo_code = models.TextField(null=True, blank=True)
    payment_message_id = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f'#{self.external_id} {self.name}'


class Message(models.Model):
    user_from = models.ForeignKey(
        to='Profile',
        on_delete=models.PROTECT,
        related_name='user_from',
        null=True,
    )
    user_to = models.ForeignKey(
        to='Profile',
        on_delete=models.PROTECT,
        related_name='user_to',
        null=True,
    )
    text = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(
        auto_now_add=True,
    )
    related_to = models.IntegerField()  # Order ID or -1 if tech support
    file_id = models.TextField(null=True, blank=True)
    photo_id = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'Message {self.pk} from {self.user_from} to {self.user_to}'


class Order(models.Model):
    customer = models.ForeignKey(
        to='Profile',
        related_name='customer',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    freelancer = models.ForeignKey(
        to='Profile',
        related_name='freelancer',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    date = models.DateTimeField(
        auto_now_add=True,
    )

    subject = models.TextField()
    type = models.TextField()
    deadline = models.TextField()
    description = models.TextField()
    plagiarism = models.TextField(null=True, blank=True)

    # document,file_id,,photo,file_id
    files = models.TextField(null=True, blank=True)

    # new, approved, paid, canceled, done
    status = models.TextField()

    price = models.IntegerField(null=True, blank=True)
    rate = models.IntegerField(null=True, blank=True)
    promo_code = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'{self.pk} from {self.customer}'


class OrderFeedback(models.Model):
    freelancer = models.ForeignKey(
        to='Profile',
        related_name='user',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    date = models.DateTimeField(auto_now_add=True)
    comment = models.TextField()
    price = models.IntegerField(null=True, blank=True)

    order = models.ForeignKey(
        to='Order',
        related_name='order',
        on_delete=models.PROTECT
    )

    def __str__(self):
        return f'{self.pk} from {self.freelancer}'


# class FreelanceApplication(models.Model):
#     profile = models.ForeignKey(
#         to='Profile',
#         on_delete=models.PROTECT,
#     )
#     date = models.DateTimeField(
#         auto_now_add=True,
#     )
#     description = models.TextField()
#
#     def __str__(self):
#         return f'{self.pk} from {self.profile}'


class MoneyOutRequest(models.Model):
    profile = models.ForeignKey(
        to='Profile',
        on_delete=models.PROTECT,
    )
    date = models.DateTimeField(
        auto_now_add=True,
    )
    sum = models.IntegerField()
    requisites = models.TextField()
    status = models.TextField(default='processing')  # processing, done, cancelled

    def __str__(self):
        return f'{self.sum} from {self.profile}'


class MoneyInRequest(models.Model):
    profile = models.ForeignKey(
        to='Profile',
        on_delete=models.PROTECT,
    )
    date = models.DateTimeField(
        auto_now_add=True,
    )
    sum = models.IntegerField()
    status = models.TextField(default='processing')  # processing, done, cancelled

    def __str__(self):
        return f'{self.sum} from {self.profile}'
