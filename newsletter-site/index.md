---
layout: default
title: Revue du matin
---

{% assign editions = site.posts | where: "lang", "fr" %}
<ul>
{% for post in editions limit:30 %}
  <li><a href="{{ post.url | relative_url }}">{{ post.date | date: "%d/%m/%Y" }}</a></li>
{% else %}
  <li><em>Aucune édition pour l'instant</em></li>
{% endfor %}
</ul>
