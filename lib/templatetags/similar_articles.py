from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='similar_articles')
def similar_articles(articles, appname_override=False, leader_override=False):
    """
    Generate the unordered list
    of related articles from Taggit
    taking into account the different apps

    Create a list, convert to str, mark_safe
    """
    leader = "<p>If you found this article "
    leader += "interesting you may enjoy the "
    leader += "following similar publications:</p>"
    if leader_override:
        leader = "<p>%s</p>" % leader_override

    uo_start = "<ul>"
    uo_end = "</ul>"
    uo_contents = []
    footer = "<p><small>Format: Title [Website Section: Publication Date, YYYY-MM-DD]</small></p>"
    if len(articles) > 0:
        for a in articles:
            list_item = []
            list_item.append("<li>")

            try:
                list_item.append('<a href="%s">' % a.get_absolute_url())
            except:
                list_item.append('<a href="#">')

            # Some apps will have a title, others will have
            # other identifiers. Try and catch them all here
            try:
                list_item.append(a.title) # Newsletter
            except AttributeError:
                try:
                    list_item.append(a.package) # Manual & Software
                except AttributeError:
                    try:
                        list_item.append(a.name) # Product
                    except AttributeError:
                        list_item.append(" &ndash; ")

            list_item.append(" [ ")

            if appname_override:
                list_item.append("%s: " % appname_override)
            else:
                try:
                    list_item.append("%s: " % a._meta.verbose_name)
                except:
                    list_item.append(" ")

            try:
                list_item.append(a.pub_date.strftime("%Y-%m-%d "))
            except:
                list_item.append(" ")

            # For DMS Newsletter
            try:
                a.newsletter.volume
                list_item.append("Volume %s, " % a.newsletter.volume)
            except:
                list_item.append("")

            try:
                a.newsletter.number
                list_item.append("Number %s" % a.newsletter.number)
            except:
                list_item.append("")

            list_item.append(" ] ")
            list_item.append("</a>")
            list_item.append("</li>")
            uo_contents.append("".join(list_item))
    else:
        uo_contents.append("<li>No related articles available</li>")

    return mark_safe("%s %s %s %s %s" % (leader,
                                      uo_start,
                                      "".join(uo_contents),
                                      uo_end,
                                      footer))
