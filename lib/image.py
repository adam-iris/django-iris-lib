from django.db import models

def image_file_name(instance, filename):
    """
    A static method that just calls the equivalent method on the provided instance.
    This is passed to ImageField.upload_to, allowing the model class to define the path for uploaded images.
    """
    return instance.image_file_name(filename)

class BaseImage(models.Model):
    """
    An abstract base class for an uploadable image.
    """
    DISPLAY_WIDTH_HELP = """Display height will be automatically calculated from the width."""

    image = models.ImageField(blank=True,
                              max_length=200,
                              upload_to=image_file_name,
                              height_field='img_height',
                              width_field='img_width')
    img_width = models.PositiveIntegerField(editable=False)
    img_height = models.PositiveIntegerField(editable=False)
    display_width = models.IntegerField(blank=True,
                                        help_text=DISPLAY_WIDTH_HELP)
    display_height = models.IntegerField(blank=True, editable=False)

    def image_file_name(self, filename):
        """
        Return the appropriate upload path for the given filename.
        The subclass should implement this.
        """
        raise NotImplementedError()

    def save(self, *args, **kwargs):
        """
        Calculate the display size when saving
        """
        if self.image:
            if self.display_width:
                ratio = float(self.display_width) / float(self.img_width)
                self.display_height = int(self.img_height * ratio)
            else:
                self.display_width = self.img_width
                self.display_height = self.img_height
            super(BaseImage, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'%s' % (self.image)

    class Meta:
        abstract = True
        ordering = ('image',)

