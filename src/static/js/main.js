(function () {
  'use strict';

  /* липкая шапка ------------------------------------------------------- */
  var shell = document.querySelector('.nav-shell');
  var stuck = false;
  var onScroll = function () {
    // гистерезис, чтобы класс не мигал на границе
    var y = window.scrollY;
    if (!stuck && y > 40) { stuck = true; shell.classList.add('is-stuck'); }
    else if (stuck && y < 12) { stuck = false; shell.classList.remove('is-stuck'); }
  };
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* мобильное меню ------------------------------------------------------ */
  var links = document.getElementById('navMenu');
  var panel = document.getElementById('navPanel');
  var burger = document.getElementById('navBurger');

  var closeMenu = function (keepLock) {
    panel.classList.remove('is-open');
    burger.classList.remove('is-open');
    burger.setAttribute('aria-expanded', 'false');
    if (keepLock !== true) document.body.classList.remove('is-locked');
  };

  burger.addEventListener('click', function () {
    var open = !panel.classList.contains('is-open');
    panel.classList.toggle('is-open', open);
    burger.classList.toggle('is-open', open);
    burger.setAttribute('aria-expanded', String(open));
    document.body.classList.toggle('is-locked', open);
  });

  document.getElementById('navClose').addEventListener('click', function () { closeMenu(); });

  panel.addEventListener('click', function (e) {
    // открывается модалка — меню закрываем, но прокрутку страницы оставляем заблокированной
    if (e.target.hasAttribute('data-modal-open')) closeMenu(true);
  });

  links.addEventListener('click', function (e) {
    if (e.target.tagName === 'A') closeMenu();
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeMenu();
  });


  /* активный пункт меню по текущей секции -------------------------------- */
  var menuLinks = Array.prototype.slice.call(links.querySelectorAll('a'));
  var targets = menuLinks
    .map(function (a) {
      var id = a.getAttribute('href');
      return { link: a, el: id === '#top' ? document.body : document.querySelector(id) };
    })
    .filter(function (t) { return t.el; });

  var setActive = function (link) {
    menuLinks.forEach(function (a) { a.classList.toggle('is-active', a === link); });
  };

  var spy = function () {
    var line = window.scrollY + 140;   // поправка на высоту липкой шапки
    var current = targets[0];

    targets.forEach(function (t) {
      if (t.el === document.body) return;
      if (t.el.offsetTop <= line) current = t;
    });

    // у самого низа страницы подсвечиваем последнюю секцию
    if (document.body.scrollHeight > window.innerHeight + 10 &&
        window.innerHeight + window.scrollY >= document.body.scrollHeight - 4) {
      current = targets[targets.length - 1];
    }
    setActive(current.link);
  };

  window.addEventListener('scroll', spy, { passive: true });
  window.addEventListener('resize', spy);
  spy();

  menuLinks.forEach(function (a) {
    a.addEventListener('click', function () { setActive(a); });
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

  /* слайдеры: «Наши клиенты» и отзывы на телефоне ------------------------- */
  var setupSlider = function (track, dotsBox, arrows) {
    if (!track) return;

    var slides = Array.prototype.slice.call(track.children);
    if (!slides.length) return;

    var current = Math.max(0, slides.findIndex(function (s) { return s.classList.contains('is-active'); }));

    var dots = !dotsBox ? [] : slides.map(function (slide, i) {
      var b = document.createElement('button');
      b.type = 'button';
      b.setAttribute('aria-label', 'Слайд ' + (i + 1));
      b.addEventListener('click', function () { goTo(i); });
      dotsBox.appendChild(b);
      return b;
    });

    var centerOf = function (slide) {
      return slide.offsetLeft - (track.clientWidth - slide.offsetWidth) / 2;
    };

    var nearest = function () {
      var mid = track.scrollLeft + track.clientWidth / 2;
      var best = 0, bestDist = Infinity;
      slides.forEach(function (s, i) {
        var d = Math.abs(s.offsetLeft + s.offsetWidth / 2 - mid);
        if (d < bestDist) { bestDist = d; best = i; }
      });
      return best;
    };

    var mark = function (i) {
      current = i;
      slides.forEach(function (s, n) { s.classList.toggle('is-active', n === i); });
      dots.forEach(function (d, n) { d.classList.toggle('is-active', n === i); });
    };

    var goTo = function (i) {
      i = Math.max(0, Math.min(slides.length - 1, i));
      mark(i);
      window.setTimeout(function () {
        track.scrollTo({ left: centerOf(slides[i]), behavior: 'smooth' });
      }, 20);
    };

    (arrows || []).forEach(function (btn) {
      btn.addEventListener('click', function () {
        goTo(current + parseInt(btn.dataset.slide, 10));
      });
    });

    var timer = null;
    track.addEventListener('scroll', function () {
      if (timer) return;
      timer = window.setTimeout(function () {
        timer = null;
        var i = nearest();
        if (i !== current) mark(i);   // подстройка под свайп
      }, 60);
    }, { passive: true });

    var center = function () {
      // на десктопе отзывы стоят колонкой — центрировать нечего
      if (track.scrollWidth > track.clientWidth + 4) track.scrollLeft = centerOf(slides[current]);
    };

    mark(current);
    window.setTimeout(center, 30);
    window.addEventListener('resize', center);
  };

  setupSlider(
    document.getElementById('slider'),
    document.getElementById('sliderDots'),
    Array.prototype.slice.call(document.querySelectorAll('.work .arrow'))
  );

  setupSlider(
    document.getElementById('reviewsTrack'),
    document.getElementById('reviewsDots'),
    []
  );

  /* калькулятор списания -------------------------------------------------- */
  var lastCalc = null;
  var calcForm = document.getElementById('calcForm');

  if (calcForm) {
    var MONTHS = 60;
    var DISCOUNT = 0.10;

    var money = function (n) {
      return Math.round(n).toLocaleString('ru-RU').replace(/\u00a0/g, ' ') + ' ₸';
    };
    var num = function (el) {
      return parseInt((el.value || '').replace(/\D/g, ''), 10) || 0;
    };

    // разделяем разряды прямо при вводе
    calcForm.querySelectorAll('input').forEach(function (input) {
      input.addEventListener('input', function () {
        var digits = (input.value || '').replace(/\D/g, '').slice(0, 12);
        input.value = digits ? digits.replace(/\B(?=(\d{3})+(?!\d))/g, ' ') : '';
      });
    });

    // анимация прогресса: кольцо + пошаговые галочки
    var ring = document.getElementById('calcRing');
    var pct = document.getElementById('calcPct');
    var steps = Array.prototype.slice.call(document.querySelectorAll('#calcSteps li'));
    var LENGTH = 214;
    var slow = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    var runProgress = function (done) {
      var duration = slow ? 1600 : 300;
      var start = null;

      steps.forEach(function (li) { li.classList.remove('is-done', 'is-active'); });
      ring.style.strokeDashoffset = LENGTH;
      pct.textContent = '0%';

      var frame = function (now) {
        if (start === null) start = now;
        var p = Math.min(1, (now - start) / duration);
        var eased = 1 - Math.pow(1 - p, 3);

        ring.style.strokeDashoffset = LENGTH * (1 - eased);
        pct.textContent = Math.round(eased * 100) + '%';

        var reached = Math.min(steps.length, Math.floor(eased * steps.length + 0.0001));
        steps.forEach(function (li, i) {
          li.classList.toggle('is-done', i < reached);
          li.classList.toggle('is-active', i === reached);
        });

        if (p >= 1) {
          window.clearInterval(timer);
          steps.forEach(function (li) { li.classList.add('is-done'); li.classList.remove('is-active'); });
          window.setTimeout(done, 220);
        }
      };

      var timer = window.setInterval(function () { frame(Date.now()); }, 40);
      frame(Date.now());
    };

    calcForm.addEventListener('submit', function (e) {
      e.preventDefault();

      var debt = num(document.getElementById('calcDebt'));
      var pay = num(document.getElementById('calcPay'));
      var income = num(document.getElementById('calcIncome'));
      var error = document.getElementById('calcError');
      var fields = document.getElementById('calcFields');
      var loader = document.getElementById('calcLoader');

      if (!debt) {
        error.hidden = false;
        return;
      }
      error.hidden = true;

      var newDebt = debt * (1 - DISCOUNT);
      var monthly = newDebt / MONTHS;

      lastCalc = { debt: debt, pay: pay, income: income, monthly: Math.round(monthly), money: money };

      // на время расчёта показываем прогресс вместо полей, затем открываем окно с результатом
      calcForm.style.minHeight = calcForm.offsetHeight + 'px';
      fields.hidden = true;
      loader.hidden = false;
      runProgress(function () {
        loader.hidden = true;
        fields.hidden = false;
        calcForm.style.minHeight = '';
        document.dispatchEvent(new CustomEvent('calc:done'));
      });
    });
  }

  /* модальное окно заявки ------------------------------------------------ */
  var modal = document.getElementById('leadModal');

  if (modal) {
    var card = modal.querySelector('.modal-card');
    var body = modal.querySelector('.modal-body');
    var done = modal.querySelector('.modal-done');
    var mForm = document.getElementById('modalForm');
    var lastFocused = null;

    var sumBox = document.getElementById('modalSum');
    var title = document.getElementById('modalTitle');

    var fillCalc = function (withCalc) {
      var map = {
        m_calc_debt: withCalc ? lastCalc.debt : '',
        m_calc_payments: withCalc && lastCalc.pay ? lastCalc.pay : '',
        m_calc_income: withCalc && lastCalc.income ? lastCalc.income : '',
        m_calc_result: withCalc ? lastCalc.monthly : ''
      };
      Object.keys(map).forEach(function (id) {
        var el = document.getElementById(id);
        if (el) el.value = map[id];
      });

      if (withCalc) {
        title.textContent = 'Ваш новый ежемесячный платеж будет составлять';
        sumBox.innerHTML = lastCalc.money(lastCalc.monthly) + '<span>в месяц</span>';
        sumBox.hidden = false;
      } else {
        title.textContent = 'Бесплатная консультация';
        sumBox.hidden = true;
      }
    };

    var openModal = function () {
      lastFocused = document.activeElement;
      body.hidden = false;
      done.hidden = true;
      modal.hidden = false;
      document.body.classList.add('is-locked');
      var first = body.querySelector('input');
      if (first) first.focus({ preventScroll: true });
    };

    var closeModal = function () {
      modal.hidden = true;
      document.body.classList.remove('is-locked');
      if (lastFocused) lastFocused.focus({ preventScroll: true });
    };

    document.querySelectorAll('[data-modal-open]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        fillCalc(false);
        openModal();
      });
    });

    // расчёт готов — показываем сумму в отдельном окне
    document.addEventListener('calc:done', function () {
      fillCalc(!!lastCalc);
      openModal();
    });
    modal.querySelectorAll('[data-modal-close]').forEach(function (btn) {
      btn.addEventListener('click', closeModal);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !modal.hidden) closeModal();
    });

    mForm.addEventListener('submit', function (e) {
      e.preventDefault();

      var submit = mForm.querySelector('button[type="submit"]');
      submit.disabled = true;
      submit.textContent = 'Отправляем…';
      mForm.querySelectorAll('.errorlist').forEach(function (ul) { ul.innerHTML = ''; });

      fetch(mForm.action, {
        method: 'POST',
        body: new FormData(mForm),
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
      })
        .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
        .then(function (res) {
          submit.disabled = false;
          submit.textContent = 'Отправить';

          if (res.ok && res.data.ok) {
            body.hidden = true;
            done.hidden = false;
            card.scrollTop = 0;
            mForm.reset();
            return;
          }

          Object.keys(res.data.errors || {}).forEach(function (name) {
            var ul = mForm.querySelector('[data-error-for="' + name + '"]');
            if (ul) ul.innerHTML = res.data.errors[name].map(function (t) { return '<li>' + t + '</li>'; }).join('');
          });
        })
        .catch(function () {
          submit.disabled = false;
          submit.textContent = 'Отправить';
          var ul = mForm.querySelector('[data-error-for="phone"]');
          if (ul) ul.innerHTML = '<li>Не удалось отправить. Попробуйте ещё раз или позвоните нам.</li>';
        });
    });
  }
})();
