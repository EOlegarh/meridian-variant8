from django import template
register=template.Library()
@register.filter
def photo(tour):
    if tour.image:return tour.image.url
    names={'Алтай':'altai','Карелия':'karelia','Стамбул':'istanbul'}
    name=names.get(tour.hotel.direction.name)
    return '/static/images/'+name+'.webp' if name else ''
