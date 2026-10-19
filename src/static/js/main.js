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
  if (!burger) return;   // на странице «Спасибо» нет меню и форм

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

  /* слайдер «Наши клиенты» ----------------------------------------------- */
  var setupClientSlider = function () {
    var track = document.getElementById('slider');
    var dotsBox = document.getElementById('sliderDots');
    var arrows = Array.prototype.slice.call(document.querySelectorAll('.work .arrow'));

    if (!track) return;
    var slides = Array.prototype.slice.call(track.children);
    var count = slides.length;
    if (!count) return;

    var current = 0;
    var activeIndex = slides.findIndex(function (s) { return s.classList.contains('is-active'); });
    if (activeIndex >= 0) current = activeIndex;

    var dots = !dotsBox ? [] : slides.map(function (slide, i) {
      var b = document.createElement('button');
      b.type = 'button';
      b.setAttribute('aria-label', 'Слайд ' + (i + 1));
      b.addEventListener('click', function () { goTo(i); });
      dotsBox.appendChild(b);
      return b;
    });

    var render = function () {
      slides.forEach(function (slide, i) {
        slide.classList.remove('is-active', 'is-prev', 'is-next', 'is-hidden');
        var diff = (i - current + count) % count;
        if (diff === 0) {
          slide.classList.add('is-active');
        } else if (diff === 1) {
          slide.classList.add('is-next');
        } else if (diff === count - 1) {
          slide.classList.add('is-prev');
        } else {
          slide.classList.add('is-hidden');
        }

        // Если видео не активно — ставим на паузу
        if (diff !== 0) {
          var v = slide.querySelector('video');
          if (v && !v.paused) v.pause();
        }
      });

      dots.forEach(function (dot, i) {
        dot.classList.toggle('is-active', i === current);
      });
    };

    var goTo = function (i) {
      current = (i + count) % count;
      render();
    };

    arrows.forEach(function (btn) {
      btn.addEventListener('click', function () {
        var dir = parseInt(btn.dataset.slide, 10) || 1;
        goTo(current + dir);
      });
    });

    slides.forEach(function (slide, i) {
      slide.addEventListener('click', function (e) {
        if (!slide.classList.contains('is-active')) {
          e.preventDefault();
          goTo(i);
        }
      });
    });

    // Свайпы на мобильных устройствах
    var touchStartX = 0;
    var touchStartY = 0;
    track.addEventListener('touchstart', function (e) {
      if (e.touches.length === 1) {
        touchStartX = e.touches[0].clientX;
        touchStartY = e.touches[0].clientY;
      }
    }, { passive: true });

    track.addEventListener('touchend', function (e) {
      if (e.changedTouches.length === 1) {
        var dx = e.changedTouches[0].clientX - touchStartX;
        var dy = e.changedTouches[0].clientY - touchStartY;
        if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy)) {
          if (dx < 0) {
            goTo(current + 1);
          } else {
            goTo(current - 1);
          }
        }
      }
    }, { passive: true });

    render();
  };

  setupClientSlider();

  /* анкета: 3 вопроса вместо калькулятора ------------------------------- */
  var lastCalc = null;
  var quizCard = document.getElementById('quizCard');

  if (quizCard) {
    var MONTHS = 60;
    var DISCOUNT = 0.10;

    var money = function (n) {
      return Math.round(n).toLocaleString('ru-RU').replace(/ /g, ' ') + ' ₸';
    };
    var withSpaces = function (digits) {
      return digits ? String(digits).replace(/\B(?=(\d{3})+(?!\d))/g, ' ') : '';
    };

    var answers = { debt: 0, has_income: '', credit_types: '' };
    var steps = [1, 2, 3].map(function (n) { return document.getElementById('quizStep' + n); });
    var debtInput = document.getElementById('quizDebtInput');
    var debtError = document.getElementById('quizDebtError');
    var incomeError = document.getElementById('quizIncomeError');
    var creditError = document.getElementById('quizCreditError');

    var showStep = function (n) {
      steps.forEach(function (el, i) { el.classList.toggle('is-active', i === n - 1); });
      var pctValue = Math.round(n / 3 * 100);
      document.getElementById('quizStepCurrent').textContent = n;
      document.getElementById('quizStepPercent').textContent = pctValue + '%';
      document.getElementById('quizProgressFill').style.width = pctValue + '%';

      // на телефоне возвращаем карточку в зону видимости
      var rect = quizCard.getBoundingClientRect();
      if (rect.top < 70) window.scrollTo({ top: window.scrollY + rect.top - 90, behavior: 'smooth' });
    };

    // вопрос 1 — сумма кредитов, разряды разделяем прямо при вводе
    debtInput.addEventListener('input', function () {
      var digits = (debtInput.value || '').replace(/\D/g, '').slice(0, 12);
      debtInput.value = withSpaces(digits);
      if (digits) debtError.hidden = true;
    });

    quizCard.querySelectorAll('.quiz-chip').forEach(function (chip) {
      chip.addEventListener('click', function () {
        debtInput.value = withSpaces(chip.getAttribute('data-debt'));
        debtError.hidden = true;
      });
    });

    // процедура не подходит — показываем окно отказа, в CRM ничего не уходит
    var MIN_DEBT = 4700000;
    var REJECT = {
      debt: 'Для восстановления платежеспособности сумма долга должна составлять более 4 700 000 ₸.',
      income: 'Для восстановления платежеспособности необходимо иметь официальный подтверждённый доход. ' +
        'Без официального дохода пройти процедуру восстановления платежеспособности не получится.',
      credits: 'Если у вас только ипотека или только автокредит, восстановление платежеспособности вам не подходит. ' +
        'Для прохождения процедуры у вас должны быть потребительские кредиты.'
    };
    var reject = function (reason) {
      document.dispatchEvent(new CustomEvent('calc:reject', { detail: REJECT[reason] }));
    };

    // «Пройти заново» — сбрасываем ответы и возвращаемся к первому вопросу
    document.addEventListener('quiz:restart', function () {
      answers = { debt: 0, has_income: '', credit_types: '' };
      lastCalc = null;
      debtInput.value = '';
      quizCard.querySelectorAll('.quiz-option.is-selected').forEach(function (o) { o.classList.remove('is-selected'); });
      showStep(1);
    });

    document.getElementById('quizNext1').addEventListener('click', function () {
      var debt = parseInt((debtInput.value || '').replace(/\D/g, ''), 10) || 0;
      if (debt < 100000) {
        debtError.hidden = false;
        debtInput.focus();
        return;
      }
      if (debt < MIN_DEBT) { reject('debt'); return; }
      answers.debt = debt;
      showStep(2);
    });

    // вопросы 2 и 3 — выбор одного варианта
    var bindOptions = function (step, key, error, onPick) {
      var options = steps[step - 1].querySelectorAll('.quiz-option');
      options.forEach(function (opt) {
        opt.addEventListener('click', function () {
          options.forEach(function (o) { o.classList.toggle('is-selected', o === opt); });
          answers[key] = opt.getAttribute('data-val') || '';
          error.hidden = true;
          if (onPick) onPick();
        });
      });
    };

    var goAfterIncome = function () {
      if (answers.has_income === 'Нет') { reject('income'); return; }
      showStep(3);
    };

    bindOptions(2, 'has_income', incomeError, function () {
      window.setTimeout(goAfterIncome, 260);
    });
    bindOptions(3, 'credit_types', creditError);

    document.getElementById('quizPrev2').addEventListener('click', function () { showStep(1); });
    document.getElementById('quizPrev3').addEventListener('click', function () { showStep(2); });
    document.getElementById('quizNext2').addEventListener('click', function () {
      if (!answers.has_income) { incomeError.hidden = false; return; }
      goAfterIncome();
    });

    // анимация прогресса: кольцо + пошаговые галочки
    var ring = document.getElementById('calcRing');
    var pct = document.getElementById('calcPct');
    var loaderSteps = Array.prototype.slice.call(document.querySelectorAll('#calcSteps li'));
    var LENGTH = 214;
    var slow = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    var runProgress = function (done) {
      var duration = slow ? 1600 : 300;
      var start = null;

      loaderSteps.forEach(function (li) { li.classList.remove('is-done', 'is-active'); });
      ring.style.strokeDashoffset = LENGTH;
      pct.textContent = '0%';

      var frame = function (now) {
        if (start === null) start = now;
        var p = Math.min(1, (now - start) / duration);
        var eased = 1 - Math.pow(1 - p, 3);

        ring.style.strokeDashoffset = LENGTH * (1 - eased);
        pct.textContent = Math.round(eased * 100) + '%';

        var reached = Math.min(loaderSteps.length, Math.floor(eased * loaderSteps.length + 0.0001));
        loaderSteps.forEach(function (li, i) {
          li.classList.toggle('is-done', i < reached);
          li.classList.toggle('is-active', i === reached);
        });

        if (p >= 1) {
          window.clearInterval(timer);
          loaderSteps.forEach(function (li) { li.classList.add('is-done'); li.classList.remove('is-active'); });
          window.setTimeout(done, 220);
        }
      };

      var timer = window.setInterval(function () { frame(Date.now()); }, 40);
      frame(Date.now());
    };

    document.getElementById('quizNext3').addEventListener('click', function () {
      if (!answers.credit_types) { creditError.hidden = false; return; }
      if (answers.credit_types === 'Только ипотека' || answers.credit_types === 'Только автокредит') {
        reject('credits');
        return;
      }

      var monthly = answers.debt * (1 - DISCOUNT) / MONTHS;
      lastCalc = {
        debt: answers.debt,
        has_income: answers.has_income,
        credit_types: answers.credit_types,
        monthly: Math.round(monthly),
        money: money
      };

      // на время расчёта показываем прогресс вместо вопросов, затем открываем окно с результатом
      var fields = document.getElementById('calcFields');
      var loader = document.getElementById('calcLoader');
      quizCard.style.minHeight = quizCard.offsetHeight + 'px';
      fields.hidden = true;
      loader.hidden = false;
      runProgress(function () {
        loader.hidden = true;
        fields.hidden = false;
        quizCard.style.minHeight = '';
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
    var rejectBox = modal.querySelector('.modal-reject');
    var mForm = document.getElementById('modalForm');
    var lastFocused = null;

    var sumBox = document.getElementById('modalSum');
    var title = document.getElementById('modalTitle');

    var fillCalc = function (withCalc) {
      var map = {
        m_calc_debt: withCalc ? lastCalc.debt : '',
        m_calc_result: withCalc ? lastCalc.monthly : '',
        m_has_income: withCalc ? lastCalc.has_income : '',
        m_credit_types: withCalc ? lastCalc.credit_types : ''
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
      rejectBox.hidden = true;
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

    // процедура не подходит — окно отказа без формы заявки
    document.addEventListener('calc:reject', function (e) {
      lastFocused = document.activeElement;
      document.getElementById('rejectText').textContent = e.detail;
      body.hidden = true;
      done.hidden = true;
      rejectBox.hidden = false;
      modal.hidden = false;
      document.body.classList.add('is-locked');
    });
    modal.querySelector('[data-quiz-restart]').addEventListener('click', function () {
      closeModal();
      document.dispatchEvent(new CustomEvent('quiz:restart'));
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
            if (typeof fbq === 'function') {
              try { fbq('track', 'Lead'); } catch(e) {}
            }
            if (typeof ttq === 'object' && typeof ttq.track === 'function') {
              try { ttq.track('SubmitForm'); } catch(e) {}
            }
            if (res.data.redirect_url) {
              window.location.href = res.data.redirect_url;
              return;
            }
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

  /* маска ввода номера телефона (+7 (7XX) XXX-XX-XX) -------------------- */
  function initPhoneMask(input) {
    if (!input) return;

    input.setAttribute('type', 'tel');
    input.setAttribute('inputmode', 'tel');
    input.setAttribute('autocomplete', 'tel');

    function getDigits(str) {
      return (str || '').replace(/\D/g, '');
    }

    function formatFromDigits(rawDigits) {
      if (!rawDigits) return '';

      var digits = rawDigits;
      // Если начинается с 7 или 8 и длина больше 1, отсекаем префикс страны
      if (digits.length > 0 && (digits[0] === '7' || digits[0] === '8')) {
        digits = digits.substring(1);
      }
      digits = digits.substring(0, 10);

      var res = '+7';
      if (digits.length > 0) {
        res += ' (' + digits.substring(0, 3);
      }
      if (digits.length >= 3) {
        res += ') ' + digits.substring(3, 6);
      }
      if (digits.length >= 6) {
        res += '-' + digits.substring(6, 8);
      }
      if (digits.length >= 8) {
        res += '-' + digits.substring(8, 10);
      }
      return res;
    }

    // Корректная обработка Backspace для удаления символов и скобок
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Backspace') {
        var start = input.selectionStart;
        var end = input.selectionEnd;

        // Если выделен диапазон текста
        if (start !== end) {
          return;
        }

        if (start > 0) {
          var val = input.value;
          var prevChar = val.charAt(start - 1);

          // Если символ перед курсором — разделитель (дефис, скобка, пробел)
          if (/\D/.test(prevChar)) {
            e.preventDefault();
            // Ищем последнюю цифру перед курсором
            var lastDigitIndex = -1;
            for (var i = start - 1; i >= 0; i--) {
              if (/\d/.test(val.charAt(i))) {
                lastDigitIndex = i;
                break;
              }
            }

            if (lastDigitIndex > 1) { // не удаляем +7
              var newVal = val.slice(0, lastDigitIndex) + val.slice(lastDigitIndex + 1);
              var d = getDigits(newVal);
              input.value = d.length > 1 ? formatFromDigits(d) : '';
              var newCursor = Math.max(0, lastDigitIndex);
              input.setSelectionRange(newCursor, newCursor);
            } else {
              input.value = '';
            }
          }
        }
      }
    });

    input.addEventListener('input', function () {
      var digits = getDigits(input.value);
      if (!digits || digits.length === 0) {
        input.value = '';
        return;
      }

      // Если ввели только 7 или 8
      if (digits === '7' || digits === '8') {
        input.value = '+7 (';
        return;
      }

      input.value = formatFromDigits(digits);
    });

    input.addEventListener('paste', function (e) {
      e.preventDefault();
      var pasted = (e.clipboardData || window.clipboardData).getData('text');
      var digits = getDigits(pasted);
      input.value = formatFromDigits(digits);
    });

    input.addEventListener('focus', function () {
      if (!input.value) {
        input.value = '+7 (';
      }
    });

    input.addEventListener('blur', function () {
      var digits = getDigits(input.value);
      if (digits.length <= 1) {
        input.value = '';
      }
    });
  }

  document.querySelectorAll('input[name="phone"], input[type="tel"], #id_phone, #m_phone').forEach(initPhoneMask);
})();
