// Clínica Dental Ontiveros — interacciones (sin dependencias)
(function(){
  var root = document.documentElement;

  // Menú móvil
  var burger = document.querySelector('.burger');
  function closeNav(){ document.body.classList.remove('nav-open'); if(burger) burger.setAttribute('aria-expanded','false'); }
  if(burger){
    burger.addEventListener('click', function(){
      var open = document.body.classList.toggle('nav-open');
      burger.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
    document.querySelectorAll('.nav a').forEach(function(a){ a.addEventListener('click', closeNav); });
  }
  document.addEventListener('keydown', function(e){ if(e.key === 'Escape'){ closeNav(); closeLb(); } });

  // Cabecera con sombra al bajar
  var onScroll = function(){ root.classList.toggle('scrolled', window.scrollY > 10); };
  window.addEventListener('scroll', onScroll, {passive:true}); onScroll();

  // "Te llamamos": despliega el mini formulario
  var cbBtn = document.querySelector('[data-open-callback]');
  var cbPanel = document.getElementById('cb-panel');
  if(cbBtn && cbPanel){
    cbBtn.addEventListener('click', function(){
      var open = cbPanel.hasAttribute('hidden');
      if(open){ cbPanel.removeAttribute('hidden'); cbPanel.querySelector('input[name=nombre]').focus(); }
      else cbPanel.setAttribute('hidden','');
      cbBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  // "Pide cita para X": preselecciona el motivo en el formulario de contacto
  document.querySelectorAll('[data-motivo]').forEach(function(a){
    a.addEventListener('click', function(){ try{ sessionStorage.setItem('motivo', a.getAttribute('data-motivo')); }catch(e){} });
  });
  var sel = document.querySelector('#cita select[name=motivo]');
  if(sel){
    var m = null; try{ m = sessionStorage.getItem('motivo'); sessionStorage.removeItem('motivo'); }catch(e){}
    if(m){ for(var i=0;i<sel.options.length;i++){ if(sel.options[i].text === m){ sel.selectedIndex = i; break; } } }
  }

  // Tratamientos: barra de accesos (PC: todos visibles; móvil: botón que despliega la lista)
  var bar = document.querySelector('.chips-bar');
  var chips = document.querySelectorAll('.chips-bar .chips a');
  if(bar && chips.length){
    var pick = bar.querySelector('.tr-pick');
    var current = bar.querySelector('[data-tr-current]');
    var setOpen = function(open){ bar.classList.toggle('is-open', open); if(pick) pick.setAttribute('aria-expanded', open ? 'true' : 'false'); };
    if(pick) pick.addEventListener('click', function(){ setOpen(!bar.classList.contains('is-open')); });
    chips.forEach(function(c){ c.addEventListener('click', function(){ setOpen(false); }); });
    document.addEventListener('click', function(e){ if(!bar.contains(e.target)) setOpen(false); });
    document.addEventListener('keydown', function(e){ if(e.key === 'Escape') setOpen(false); });
    if('IntersectionObserver' in window){
      var byId = {}; chips.forEach(function(c){ byId[c.getAttribute('href').slice(1)] = c; });
      var io = new IntersectionObserver(function(entries){
        entries.forEach(function(en){
          if(en.isIntersecting && byId[en.target.id]){
            chips.forEach(function(c){ c.classList.remove('is-on'); c.removeAttribute('aria-current'); });
            var c = byId[en.target.id]; c.classList.add('is-on'); c.setAttribute('aria-current', 'true');
            if(current) current.textContent = c.textContent;
          }
        });
      }, {rootMargin:'-40% 0px -55% 0px'});
      document.querySelectorAll('.tr[id]').forEach(function(s){ io.observe(s); });
    }
  }

  // Mapa: solo se carga (con cookies de Google) si el usuario lo pide
  document.querySelectorAll('[data-map]').forEach(function(box){
    var b = box.querySelector('[data-map-load]');
    if(b) b.addEventListener('click', function(){
      var f = document.createElement('iframe');
      f.src = box.getAttribute('data-map'); f.title = 'Mapa: cómo llegar a Clínica Dental Ontiveros'; f.loading = 'lazy';
      f.referrerPolicy = 'no-referrer-when-downgrade';
      box.innerHTML = ''; box.appendChild(f);
    });
  });

  // Visor de imágenes de las galerías
  var lb = null, lastFocus = null;
  function closeLb(){ if(lb){ lb.remove(); lb = null; if(lastFocus) lastFocus.focus(); } }
  document.querySelectorAll('[data-lb]').forEach(function(a){
    a.addEventListener('click', function(e){
      e.preventDefault(); lastFocus = a;
      lb = document.createElement('div'); lb.className = 'lb'; lb.setAttribute('role','dialog'); lb.setAttribute('aria-modal','true');
      var img = document.createElement('img'); img.src = a.getAttribute('href'); img.alt = a.querySelector('img').alt;
      var btn = document.createElement('button'); btn.type = 'button'; btn.setAttribute('aria-label','Cerrar');
      btn.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 6 6 18M6 6l12 12"/></svg>';
      lb.appendChild(img); lb.appendChild(btn);
      lb.addEventListener('click', function(ev){ if(ev.target !== img) closeLb(); });
      document.body.appendChild(lb); btn.focus();
    });
  });

  // Formularios (cita y "te llamamos"): la suma la genera y comprueba el servidor (firmada)
  document.querySelectorAll('[data-form]').forEach(function(form){
    var q = form.querySelector('[data-captcha-q]');
    var loaded = false;
    var loadCaptcha = function(){
      loaded = true;
      fetch(form.action + '?captcha=1', {cache:'no-store'})
        .then(function(r){ return r.json(); })
        .then(function(j){ if(q) q.textContent = j.q + ' ='; form.token.value = j.token; form.captcha.value = ''; })
        .catch(function(){ if(q) q.textContent = '…'; });
    };
    // se pide al tocar el formulario (no en cada visita)
    form.addEventListener('focusin', function(){ if(!loaded) loadCaptcha(); });
    if(location.hash === '#' + form.id) loadCaptcha();
    form.addEventListener('submit', function(e){
      e.preventDefault();
      var msg = form.querySelector('.form-msg');
      msg.className = 'form-msg';
      if(!form.checkValidity()){ msg.className = 'form-msg err'; msg.textContent = 'Revise los campos obligatorios y la casilla de aceptación.'; return; }
      var btn = form.querySelector('button[type=submit]');
      btn.disabled = true;
      fetch(form.action, {method:'POST', body:new FormData(form)})
        .then(function(r){ return r.json(); })
        .then(function(j){
          msg.className = 'form-msg ' + (j.ok ? 'ok' : 'err');
          msg.textContent = j.message;
          if(j.ok) form.reset();
          loadCaptcha();
        })
        .catch(function(){
          msg.className = 'form-msg err';
          msg.textContent = 'No se ha podido enviar. Llámenos al 952 92 43 22 o escriba a info@clinicadentalontiveros.es.';
        })
        .finally(function(){ btn.disabled = false; });
    });
  });
})();
