---
layout: fun
title: Hello World
program: hello-world
description: Some fun project
publish: false
---

This is just an example of a single project.

<div id="example"></div>
  
<script>  
  createModule().then(module => {
    console.log(module);
    str = 'lerp result: ' + module.lerp(1, 2, 0.5);
    document.getElementById("example").innerHTML = str;
  });
</script>
