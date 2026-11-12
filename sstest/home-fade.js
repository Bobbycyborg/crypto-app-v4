document.addEventListener('DOMContentLoaded', () => {
  const stage = document.getElementById('shFadeStage');
  if (!stage) return;
  const frames = [...stage.querySelectorAll('.sh-frame')];
  if (frames.length < 2) return;

  const fadeMs = 2000;
  const autoMs = 5000;
  let index = 0;
  let busy = false;
  let autoTimer = null;

  frames.forEach((el, n) => {
    el.classList.toggle('is-current', n === 0);
  });

  function fadeTo(next) {
    if (document.body.dataset.homeView === 'grid-view') return;
    if (busy) return;

    const target = ((next % frames.length) + frames.length) % frames.length;
    if (target === index) return;

    busy = true;
    const from = frames[index];
    const to = frames[target];

    to.classList.add('is-entering');
    void to.offsetWidth;
    to.classList.add('is-current');
    from.classList.remove('is-current');

    window.setTimeout(() => {
      from.classList.remove('is-entering');
      to.classList.remove('is-entering');
      index = target;
      busy = false;
    }, fadeMs + 80);
  }

  window.shFadeTo = fadeTo;

  function bumpAuto() {
    if (autoTimer) window.clearInterval(autoTimer);
    autoTimer = window.setInterval(() => fadeTo(index + 1), autoMs);
  }

  bumpAuto();

  stage.addEventListener('click', (e) => {
    e.preventDefault();
    fadeTo(index + 1);
    bumpAuto();
  });

  window.addEventListener(
    'wheel',
    (e) => {
      if (document.body.dataset.homeView === 'grid-view') return;
      if (Math.abs(e.deltaY) < 10) return;
      e.preventDefault();
      fadeTo(index + (e.deltaY > 0 ? 1 : -1));
      bumpAuto();
    },
    { passive: false }
  );
});
