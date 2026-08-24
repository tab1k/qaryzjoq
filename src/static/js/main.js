(function () {
  'use strict';

  /* липкая шапка ------------------------------------------------------- */
  var shell = document.querySelector('.nav-shell');
  var onScroll = function () {
    shell.classList.toggle('is-stuck', window.scrollY > 20);
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* мобильное меню ------------------------------------------------------ */
  var burger = document.getElementById('navBurger');
  var links = document.getElementById('navLinks');
  burger.addEventListener('click', function () {
    links.classList.toggle('is-open');
  });
  links.addEventListener('click', function (e) {
    if (e.target.tagName === 'A') links.classList.remove('is-open');
  });

  /* аккордеон FAQ ------------------------------------------------------- */
  document.querySelectorAll('.acc-item').forEach(function (item) {
    var q = item.querySelector('.acc-q');
    var a = item.querySelector('.acc-a');

    q.addEventListener('click', function () {
      var isOpen = item.classList.contains('is-open');

      document.querySelectorAll('.acc-item.is-open').forEach(function (other) {
        other.classList.remove('is-open');
        other.querySelector('.acc-a').style.maxHeight = null;
      });

      if (!isOpen) {
        item.classList.add('is-open');
        a.style.maxHeight = a.scrollHeight + 'px';
      }
    });
  });

  /* стрелки в блоке кейсов — подсвечиваем следующий кейс ----------------- */
  var cases = Array.prototype.slice.call(document.querySelectorAll('.case'));
  var navBtns = document.querySelectorAll('.section-nav button');
  var active = 1;

  var focusCase = function (step) {
    active = (active + step + cases.length) % cases.length;
    cases.forEach(function (c, i) {
      c.classList.toggle('case--main', i === active);
    });
    cases[active].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
  };

  if (navBtns.length === 2) {
    navBtns[0].addEventListener('click', function () { focusCase(-1); });
    navBtns[1].addEventListener('click', function () { focusCase(1); });
  }

  /* маска телефона ------------------------------------------------------ */
  var phone = document.getElementById('id_phone');
  if (phone) {
    phone.addEventListener('input', function () {
      var d = phone.value.replace(/\D/g, '').replace(/^8/, '7').slice(0, 11);
      if (!d) { phone.value = ''; return; }
      var out = '+7';
      if (d.length > 1) out += ' (' + d.slice(1, 4);
      if (d.length >= 4) out += ') ' + d.slice(4, 7);
      if (d.length >= 7) out += '-' + d.slice(7, 9);
      if (d.length >= 9) out += '-' + d.slice(9, 11);
      phone.value = out;
    });
  }
})();
