document.addEventListener('DOMContentLoaded', () => {
  const project = document.getElementById('project');
  const scroller = document.getElementById('shProjectScroller');
  const overlay = document.getElementById('page-overlay');
  const info = document.getElementById('shProjectInfo');
  const overview = document.getElementById('shProjectOverview');
  const progressCurrent = project?.querySelector('.projectTopNav__progressCurrent');
  const progressTotal = project?.querySelector('.projectTopNav__progressTotal');
  const projectName = project?.querySelector('.projectTopNav__name');
  const overviewGrid = overview?.querySelector('.projectOverview__assetGrid');
  let assets = scroller ? [...scroller.querySelectorAll('.asset')] : [];

  if (!project || !scroller) return;

  const dungenessStore = {
    scrollerHTML: scroller.innerHTML,
    overviewGridHTML: overviewGrid?.innerHTML || '',
    title: projectName?.textContent || 'Dungeness',
    total: progressTotal?.textContent || '46',
    location: 'dungeness',
  };

  const manifestCache = {};

  function refreshAssets() {
    assets = [...scroller.querySelectorAll('.asset')];
  }

  function mountDungeness() {
    scroller.innerHTML = dungenessStore.scrollerHTML;
    if (overviewGrid) overviewGrid.innerHTML = dungenessStore.overviewGridHTML;
    refreshAssets();
    if (projectName) projectName.textContent = dungenessStore.title;
    if (progressTotal) progressTotal.textContent = dungenessStore.total;
    project.dataset.shProject = 'dungeness';
  }

  function mountFromManifest(manifest) {
    const base = `img/${manifest.id}/`;
    scroller.innerHTML = manifest.images
      .map(
        (file, i) =>
          `<div class="asset asset--image asset--fullscreen" data-asset-index="${i}"><div class="responsive-image"><img src="${base}${file}" alt="" loading="lazy" decoding="async"></div></div>`
      )
      .join('');
    if (overviewGrid) {
      const thumbs = manifest.images
        .map(
          (file, i) =>
            `<button type="button" class="projectOverview__button projectOverview__asset" data-asset-index="${i}"><div class="responsive-image"><img src="${base}${file}" alt="" loading="lazy"></div></button>`
        )
        .join('');
      overviewGrid.innerHTML = `${thumbs}<span class="projectOverview__overlay"></span>`;
    }
    refreshAssets();
    if (projectName) projectName.textContent = manifest.title;
    if (progressTotal) progressTotal.textContent = pad2(manifest.images.length);
    project.dataset.shProject = manifest.id;
  }

  async function ensureManifest(projectId) {
    if (manifestCache[projectId]) return manifestCache[projectId];
    if (window.SH_PROJECT_MANIFESTS?.[projectId]) {
      manifestCache[projectId] = window.SH_PROJECT_MANIFESTS[projectId];
      return manifestCache[projectId];
    }
    const res = await fetch(`img/${projectId}/manifest.json`);
    if (!res.ok) throw new Error(`manifest ${projectId}`);
    manifestCache[projectId] = await res.json();
    return manifestCache[projectId];
  }

  function pad2(n) {
    return String(n).padStart(2, '0');
  }

  function slideWidth() {
    return scroller.clientWidth || 1;
  }

  function currentIndex() {
    return Math.round(scroller.scrollLeft / slideWidth());
  }

  function goToIndex(idx) {
    const next = Math.max(0, Math.min(assets.length - 1, idx));
    scroller.scrollTo({ left: next * slideWidth(), behavior: 'smooth' });
    syncProgress();
  }

  function syncProgress() {
    if (!progressCurrent || !assets.length) return;
    progressCurrent.textContent = pad2(Math.min(assets.length, currentIndex() + 1));
  }

  function isGalleryView() {
    return (project.dataset.shPanel || 'gallery') === 'gallery';
  }

  function flattenOverviewRows() {
    const grid = overview?.querySelector('.projectOverview__assetGrid');
    if (!grid) return;
    [...grid.querySelectorAll('.projectOverview__asset')].forEach((el) => grid.appendChild(el));
    grid.querySelectorAll('.sh-overview-row').forEach((row) => row.remove());
  }

  function overviewThumbsUniform(grid) {
    if (project.dataset.shProject === 'dungeness') return false;
    const imgs = [...grid.querySelectorAll('.projectOverview__asset img')];
    if (imgs.length < 2) return false;
    const ratios = [];
    for (const img of imgs) {
      if (img.naturalWidth < 1) return false;
      ratios.push(img.naturalWidth / img.naturalHeight);
    }
    return Math.max(...ratios) - Math.min(...ratios) < 0.12;
  }

  /** layout81 — approved. Mixed-ratio galleries unchanged. */
  function fitOverviewFlex() {
    const grid = overview?.querySelector('.projectOverview__assetGrid');
    if (!grid || !overview) return;

    const count = grid.querySelectorAll('.projectOverview__asset').length;
    const gap = 6;
    const padY = 16;
    const availH = Math.max(overview.clientHeight - padY, 280);
    const countScale = Math.min(0.85, Math.pow(26 / Math.max(count, 8), 0.34));
    const uniform = overviewThumbsUniform(grid);

    let clusterW = Math.min(75, (58 + count * 0.9) * 0.75);
    let targetRows = Math.min(6, Math.max(4, Math.round(count / 9)));

    if (uniform) {
      clusterW = 75;
      targetRows = Math.min(8, Math.max(4, Math.ceil(count / 6)));
    }

    const thumbH = Math.floor(((availH - (targetRows - 1) * gap) / targetRows) * countScale);
    const h = Math.max(36, Math.min(80, thumbH));

    grid.style.setProperty('--sh-overview-thumb-h', `${h}px`);
    grid.style.setProperty('--sh-overview-cluster-w', `${clusterW}%`);
  }

  function overviewBandHeight() {
    const oStyle = getComputedStyle(overview);
    const padT = parseFloat(oStyle.paddingTop) || 0;
    const padB = parseFloat(oStyle.paddingBottom) || 0;
    return Math.max(overview.clientHeight - padT - padB, 200);
  }

  function overviewCollageHeight(grid) {
    const items = grid.querySelectorAll('.projectOverview__asset');
    if (!items.length) return 0;
    let top = Infinity;
    let bottom = 0;
    items.forEach((el) => {
      top = Math.min(top, el.offsetTop);
      bottom = Math.max(bottom, el.offsetTop + el.offsetHeight);
    });
    return Number.isFinite(top) ? bottom - top : 0;
  }

  function currentOverviewThumbH(grid) {
    const raw = getComputedStyle(grid).getPropertyValue('--sh-overview-thumb-h').trim();
    const n = parseFloat(raw);
    return Number.isFinite(n) ? n : 72;
  }

  /** Shrink thumb height 1px steps until collage fits the overview band (no crop). */
  function shrinkOverviewToBand(grid) {
    if (!grid || !overview) return;
    const bandH = overviewBandHeight();
    const minH = 24;
    let h = currentOverviewThumbH(grid);

    while (h > minH && overviewCollageHeight(grid) > bandH + 0.5) {
      h -= 1;
      grid.style.setProperty('--sh-overview-thumb-h', `${h}px`);
      void grid.offsetHeight;
    }
  }

  /** Misc only — 3 / 4 / 2 rows, larger thumbs; not layout81. */
  function fitOverviewMiscPack(grid) {
    const gap = 6;
    const bandH = overviewBandHeight();
    const pattern = [3, 4, 2];

    flattenOverviewRows();
    const items = [...grid.querySelectorAll('.projectOverview__asset')].sort(
      (a, b) => Number(a.dataset.assetIndex) - Number(b.dataset.assetIndex)
    );

    let idx = 0;
    pattern.forEach((n) => {
      const row = document.createElement('div');
      row.className = 'sh-overview-row';
      for (let k = 0; k < n && idx < items.length; k += 1, idx += 1) {
        row.appendChild(items[idx]);
      }
      if (row.childElementCount) grid.appendChild(row);
    });

    grid.style.setProperty('--sh-overview-cluster-w', '88%');

    let h = Math.floor((bandH - (pattern.length - 1) * gap) / pattern.length);
    h = Math.max(72, Math.min(150, h));
    grid.style.setProperty('--sh-overview-thumb-h', `${h}px`);
    void grid.offsetHeight;

    while (h > 48 && overviewCollageHeight(grid) > bandH + 0.5) {
      h -= 1;
      grid.style.setProperty('--sh-overview-thumb-h', `${h}px`);
      void grid.offsetHeight;
    }
  }

  function refitOverviewLayout() {
    const grid = overview?.querySelector('.projectOverview__assetGrid');
    if (!grid) return;
    if (project.dataset.shProject === 'misc') {
      fitOverviewMiscPack(grid);
      return;
    }
    fitOverviewFlex();
    offsetUniformOverviewRows(grid);
    shrinkOverviewToBand(grid);
    offsetUniformOverviewRows(grid);
  }

  function offsetUniformOverviewRows(grid) {
    if (!overviewThumbsUniform(grid)) return;
    const items = [...grid.querySelectorAll('.projectOverview__asset')];
  items.forEach((el) => el.style.removeProperty('margin-left'));
    void grid.offsetHeight;

    const rowTops = [];
    const rows = [];
    items.forEach((el) => {
      const top = el.offsetTop;
      let row = rowTops.indexOf(top);
      if (row === -1) {
        rowTops.push(top);
        row = rowTops.length - 1;
        rows.push([]);
      }
      rows[row].push(el);
    });

    rows.forEach((rowItems, row) => {
      const lead = rowItems[0];
      if (!lead) return;
      lead.style.marginLeft =
        row % 2 === 1 ? 'clamp(16px, 4.5vw, 58px)' : 'clamp(3px, 0.9vw, 16px)';
    });
  }

  function resetOverviewLayout() {
    overview?.querySelectorAll('.projectOverview__asset').forEach((el) => {
      el.classList.remove('sh-overview-enter');
      el.style.removeProperty('--sh-stagger-delay');
      el.style.removeProperty('margin-left');
      el.style.removeProperty('width');
      el.style.removeProperty('height');
      el.style.removeProperty('flex');
    });
    flattenOverviewRows();
    const grid = overview?.querySelector('.projectOverview__assetGrid');
    grid?.style.removeProperty('--sh-overview-thumb-h');
    grid?.style.removeProperty('--sh-overview-cluster-w');
  }

  function runOverviewStagger() {
    if (!overview) return;
    resetOverviewLayout();

    const layoutThenStagger = () => {
      refitOverviewLayout();
      const items = [...overview.querySelectorAll('.projectOverview__asset')].sort(
        (a, b) => Number(a.dataset.assetIndex) - Number(b.dataset.assetIndex)
      );
      items.forEach((el, i) => {
        const delay = Math.min(450, i * 16);
        el.style.setProperty('--sh-stagger-delay', `${delay}ms`);
        el.classList.add('sh-overview-enter');
      });
    };

    let laid = false;
    const layoutOnce = () => {
      if (laid) return;
      laid = true;
      requestAnimationFrame(() => requestAnimationFrame(layoutThenStagger));
    };

    const imgs = [...overview.querySelectorAll('.projectOverview__asset img')];
    const pending = imgs.filter((img) => img.naturalWidth < 1);
    if (!pending.length) {
      layoutOnce();
      return;
    }
    let left = pending.length;
    const onThumb = () => {
      left -= 1;
      if (left > 0) return;
      layoutOnce();
    };
    pending.forEach((img) => {
      img.addEventListener('load', onThumb, { once: true });
      img.addEventListener('error', onThumb, { once: true });
    });
    window.setTimeout(layoutOnce, 800);
  }

  let overviewResizeTimer = 0;
  window.addEventListener('resize', () => {
    if (!document.body.classList.contains('sh-project-panel-overview')) return;
    window.clearTimeout(overviewResizeTimer);
    overviewResizeTimer = window.setTimeout(() => refitOverviewLayout(), 80);
  });

  function setPanel(mode) {
    project.dataset.shPanel = mode || 'gallery';
    const isInfo = mode === 'info';
    const isOverview = mode === 'overview';
    document.body.classList.toggle('sh-project-panel-info', isInfo);
    document.body.classList.toggle('sh-project-panel-overview', isOverview);
    document.body.classList.toggle('sh-project-panel-open', isInfo || isOverview);
    if (isOverview) runOverviewStagger();
    else resetOverviewLayout();
  }

  async function openProject(projectId = 'dungeness') {
    setPanel('gallery');
    if (projectId === 'dungeness') {
      mountDungeness();
      document.documentElement.setAttribute('location', 'dungeness');
    } else {
      mountFromManifest(await ensureManifest(projectId));
      document.documentElement.setAttribute('location', projectId);
    }
    scroller.scrollLeft = 0;
    document.documentElement.setAttribute('type', 'project');
    document.body.classList.remove('sh-project-open');
    project.classList.remove('sh-project-is-open');
    project.hidden = false;
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        document.body.classList.add('sh-project-open');
        project.classList.add('sh-project-is-open');
        syncProgress();
        overview?.querySelectorAll('.projectOverview__asset img').forEach((img) => {
          img.loading = 'eager';
        });
      });
    });
  }

  function closeProject() {
    document.body.classList.remove('sh-project-open');
    project.classList.remove('sh-project-is-open');
    document.documentElement.setAttribute('type', 'homepage');
    document.documentElement.setAttribute('location', 'index');
    project.hidden = true;
    setPanel(null);
  }

  window.shOpenProject = openProject;
  window.shCloseProject = closeProject;

  document.getElementById('shFadeLink')?.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    const frame = document.querySelector('#shFadeStage .sh-frame.is-current');
    const pid = frame?.dataset.project || 'dungeness';
    openProject(pid);
  });

  document.getElementById('homeGridGrid')?.addEventListener('click', (e) => {
    const link = e.target.closest('.gridViewProject a');
    if (!link) return;
    e.preventDefault();
    e.stopPropagation();
    const pid = link.dataset.project || 'dungeness';
    openProject(pid).catch(() => {});
  });

  const galleryNav = document.getElementById('shGalleryNav');
  const galleryNavLeft = galleryNav?.querySelector('.shGalleryNav__half--left');
  const galleryNavRight = galleryNav?.querySelector('.shGalleryNav__half--right');
  const galleryCursor = document.getElementById('shGalleryCursor');

  function syncGalleryNavSide(clientX, clientY) {
    if (!isGalleryView() || !galleryNav) return;
    const rect = scroller.getBoundingClientRect();
    const onRight = clientX >= rect.left + rect.width / 2;
    galleryNavLeft?.classList.toggle('is-active', !onRight);
    galleryNavRight?.classList.toggle('is-active', onRight);
    if (galleryCursor) {
      galleryCursor.hidden = false;
      galleryCursor.style.left = `${clientX}px`;
      galleryCursor.style.top = `${clientY}px`;
      galleryCursor.dataset.side = onRight ? 'right' : 'left';
    }
    document.body.classList.add('sh-gallery-cursor-on');
  }

  function clearGalleryNavSide() {
    galleryNavLeft?.classList.remove('is-active');
    galleryNavRight?.classList.remove('is-active');
    if (galleryCursor) galleryCursor.hidden = true;
    document.body.classList.remove('sh-gallery-cursor-on');
  }

  project?.addEventListener('mousemove', (e) => {
    if (!isGalleryView()) return;
    if (e.target.closest('button, a, [data-action], .projectTopNav, .projectBottomNav, .projectNavCloseButton')) {
      clearGalleryNavSide();
      return;
    }
    syncGalleryNavSide(e.clientX, e.clientY);
  });
  project?.addEventListener('mouseleave', clearGalleryNavSide);

  scroller.addEventListener('scroll', syncProgress, { passive: true });

  let galleryScrolled = false;
  let galleryScrollTimer = 0;

  scroller.addEventListener(
    'scroll',
    () => {
      galleryScrolled = true;
      window.clearTimeout(galleryScrollTimer);
      galleryScrollTimer = window.setTimeout(() => {
        galleryScrolled = false;
      }, 200);
    },
    { passive: true }
  );

  scroller.addEventListener(
    'wheel',
    (e) => {
      if (!isGalleryView()) return;
      if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) return;
      if (Math.abs(e.deltaY) < 12) return;
      e.preventDefault();
      goToIndex(currentIndex() + (e.deltaY > 0 ? 1 : -1));
    },
    { passive: false }
  );

  scroller.addEventListener('click', (e) => {
    if (!isGalleryView()) return;
    if (galleryScrolled) return;
    if (e.target.closest('button, a, [data-action]')) return;
    const rect = scroller.getBoundingClientRect();
    const mid = rect.left + rect.width / 2;
    const idx = currentIndex();
    if (e.clientX >= mid) goToIndex(idx + 1);
    else goToIndex(idx - 1);
  });

  project.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;
    const action = btn.getAttribute('data-action');
  if (action === 'default') {
      if (project.dataset.shPanel && project.dataset.shPanel !== 'gallery') setPanel('gallery');
      else closeProject();
      return;
    }
    if (action === 'info') setPanel('info');
    if (action === 'overview') setPanel('overview');
  });

  overview?.addEventListener('click', (e) => {
    const thumb = e.target.closest('[data-asset-index]');
    if (!thumb) return;
    const idx = Number(thumb.dataset.assetIndex);
    const w = scroller.clientWidth || 1;
    scroller.scrollTo({ left: idx * w, behavior: 'smooth' });
    setPanel('gallery');
    syncProgress();
  });
});
