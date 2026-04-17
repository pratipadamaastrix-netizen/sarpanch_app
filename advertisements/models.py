from django.db import models
from locations.models import District, Constituency, Mandal


class HomePageHero(models.Model):
    """
    Main home-page poster shown first in the scrolling banner when active.
    Only one row should have show_first=True (enforced on save).
    """

    title = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to="hero/")
    link_url = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    show_first = models.BooleanField(
        default=True,
        help_text="When checked, this poster is the first slide (before the latest ads).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Home page hero poster"
        verbose_name_plural = "Home page hero posters"

    def __str__(self):
        return self.title or f"Hero poster #{self.pk}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.show_first and self.is_active:
            HomePageHero.objects.exclude(pk=self.pk).update(show_first=False)


class Advertisement(models.Model):
    title = models.CharField(max_length=200)

    image = models.ImageField(upload_to="ads/")

    link_url = models.URLField(blank=True, null=True)

    # Location targeting
    district = models.ForeignKey(
        District,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    constituency = models.ForeignKey(
        Constituency,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    mandal = models.ForeignKey(
        Mandal,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title