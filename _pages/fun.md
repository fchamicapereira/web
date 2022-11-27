---
layout: page
title: fun
permalink: /fun/
description:
nav: false
display_categories: [fun]
horizontal: false
program: hello-world
---

{%- for project in site.fun -%}
  {% include fun.html %}
{%- endfor %}
