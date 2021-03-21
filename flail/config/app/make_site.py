from django.contrib.sites.models import Site
new_site = Site.objects.create(domain='flail.site', name='flail.site')
print (new_site.id)
