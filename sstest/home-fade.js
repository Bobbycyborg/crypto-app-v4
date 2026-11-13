document.addEventListener('DOMContentLoaded', () => {
  const stage = document.getElementById('shFadeStage');
  if (!stage) return;

  function mountFadeFrames() {
    const items = window.shHomeGalleryItems ? window.shHomeGalleryItems() : [];
    if (items.length < 2) return null;

    stage.innerHTML = items
      .map(
        (item) =>
          `<div class="responsive-image sh-frame" data-src="${item.src}" data-project="${item.project || 'dungeness'}"><img src="${item.src}" alt="" decoding="async" loading="lazy"></div>`
      )
      .join('');
    return [...stage.querySelectorAll('.sh-frame')];
  }

  let frames = mountFadeFrames();
  if (!frames || frames.length < 2) return;

  const fadeMs = 2000;
  const autoMs = 4000;
  let index = 0;
  let busy = false;
  let busyTimer = null;
  let autoTimer = null;

  frames.forEach((el, n) => {
    el.classList.toggle('is-current', n === 0);
  });

  function syncIndexFromDom() {
    const cur = stage.querySelector('.sh-frame.is-current');
    const i = cur ? frames.indexOf(cur) : index;
    if (i >= 0) index = i;
    return index;
  }

  function wheelStep(e) {
    const ax = Math.abs(e.deltaX);
    const ay = Math.abs(e.deltaY);
    if (ax < 1 && ay < 1) return 0;
    if (ax >= ay) return e.deltaX > 0 ? 1 : -1;
    return e.deltaY > 0 ? 1 : -1;
  }

  function fadeTo(next, fromWheel = false) {
    if (document.body.dataset.homeView === 'grid-view') return;

    if (busy && fromWheel) {
      if (busyTimer) {
        window.clearTimeout(busyTimer);
        busyTimer = null;
      }
      frames.forEach((el) => el.classList.remove('is-entering'));
      syncIndexFromDom();
      busy = false;
    }
    if (busy) return;

    syncIndexFromDom();
    const target = ((next % frames.length) + frames.length) % frames.length;
    if (target === index) return;

    busy = true;
    const from = frames[index];
    const to = frames[target];

    to.classList.add('is-entering');
    void to.offsetWidth;
    to.classList.add('is-current');
    from.classList.remove('is-current');

    busyTimer = window.setTimeout(() => {
      from.classList.remove('is-entering');
      to.classList.remove('is-entering');
      index = target;
      busy = false;
      busyTimer = null;
    }, fadeMs + 40);
  }

  window.shFadeTo = fadeTo;
  window.shRebuildHomeFade = () => {
    frames = mountFadeFrames();
    if (!frames || frames.length < 2) return;
    index = 0;
    busy = false;
    if (busyTimer) window.clearTimeout(busyTimer);
    frames.forEach((el, n) => {
      el.classList.toggle('is-current', n === 0);
      el.classList.remove('is-entering');
    });
    bumpAuto();
  };

  function bumpAuto() {
    if (autoTimer) window.clearInterval(autoTimer);
    autoTimer = window.setInterval(() => {
      fadeTo(syncIndexFromDom() + 1);
    }, autoMs);
  }

  bumpAuto();

  document.addEventListener(
    'wheel',
    (e) => {
      if (document.body.classList.contains('sh-project-open')) return;
      if (document.body.dataset.homeView === 'grid-view') return;
      const step = wheelStep(e);
      if (!step) return;
      e.preventDefault();
      fadeTo(syncIndexFromDom() + step, true);
      bumpAuto();
    },
    { passive: false, capture: true }
  );
});
