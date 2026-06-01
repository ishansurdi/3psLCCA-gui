(function(){
  // Search — pure DOM, no pywebview needed
  var inp = document.getElementById('search');
  inp && (inp.oninput = function(){
    var t = this.value.toLowerCase();
    document.querySelectorAll('.nav-section').forEach(function(sec){
      var vis = false;
      sec.querySelectorAll('.nav-item').forEach(function(a){
        var show = !t || a.textContent.toLowerCase().includes(t);
        a.style.display = show ? '' : 'none';
        if (show) vis = true;
      });
      sec.querySelector('.nav-group').style.display = (!t || vis) ? '' : 'none';
    });
  });

  // Theme + navigation polling — requires pywebview (graceful no-op if absent)
  window.addEventListener('pywebviewready', function(){
    pywebview.api.get_theme().then(function(t){
      var s = document.documentElement.style;
      if (t.bg)         s.setProperty('--bg', t.bg);
      if (t.text)       s.setProperty('--tx', t.text);
      if (t.sidebar_bg) s.setProperty('--sb', t.sidebar_bg);
      if (t.accent)     s.setProperty('--ac', t.accent);
      if (t.border)     s.setProperty('--bd', t.border);
    }).catch(function(){});

    setInterval(function(){
      pywebview.api.poll_navigation().then(function(p){
        if (p) window.location.href = '../' + p.replace(/\.md$/, '.html');
      }).catch(function(){});
    }, 300);
  });
})();
