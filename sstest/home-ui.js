/** Home views (locked names): Full-view = list fade; Grid-view = grid. */
document.addEventListener('DOMContentLoaded', () => {
  const menu = document.querySelector('.menu');
  const menuBtn = document.querySelector('.menu__button');
  const viewSwitch = document.querySelector('.view-switch');
  const fullViewBtn = viewSwitch && viewSwitch.querySelector('[data-view="full-view"]');
  const gridViewBtn = viewSwitch && viewSwitch.querySelector('[data-view="grid-view"]');
  const gridRoot = document.getElementById('homeGridGrid');

  if (gridRoot && window.shHomeGalleryItems) {
    window.shHomeGalleryItems().forEach((item) => {
      const article = document.createElement('article');
      article.className = 'gridViewProject';
      const projectAttr = ` data-project="${item.project || 'dungeness'}"`;
      const title = item.title ? `<h3>${item.title}</h3>` : '<h3></h3>';
      article.innerHTML = `<a href="#"${projectAttr}><div class="gridViewProject__asset"><div class="responsive-image"><img src="${item.src}" alt="${item.title || ''}" loading="lazy"></div></div><div class="gridViewProject__description">${title}<h4></h4></div></a>`;
      gridRoot.appendChild(article);
    });
  }

  document.body.dataset.homeView = 'full-view';
  if (viewSwitch) viewSwitch.dataset.activeView = 'full-view';
  if (menu) menu.classList.remove('js-loading');

  function burgerSlot() {
    const grid = document.body.dataset.homeView === 'grid-view';
    return document.querySelector(
      grid ? '.homepageView--grid-view .homeHeader__burger' : '.homepageView--list-view .homeHeader__burger'
    );
  }

  function parkBurgerInHeader() {
    const slot = burgerSlot();
    if (menuBtn && slot) {
      slot.appendChild(menuBtn);
    }
  }

  function syncMenuOpen() {
    const open = menu && menu.classList.contains('menu--isExpanded');
    document.body.classList.toggle('sh-menu-open', !!open);
    document.body.classList.toggle(
      'sh-menu-about',
      !!(open && menu.classList.contains('menu--isAboutVisible'))
    );
    document.body.classList.toggle(
      'sh-menu-notes',
      !!(open && menu.classList.contains('menu--isNotesVisible'))
    );
  }

  function setView(view) {
    const next = view === 'grid-view' ? 'grid-view' : 'full-view';
    document.body.dataset.homeView = next;
    if (viewSwitch) viewSwitch.dataset.activeView = next;
    parkBurgerInHeader();
  }

  parkBurgerInHeader();

  fullViewBtn &&
    fullViewBtn.addEventListener('click', (e) => {
      e.preventDefault();
      setView('full-view');
    });

  gridViewBtn &&
    gridViewBtn.addEventListener('click', (e) => {
      e.preventDefault();
      setView('grid-view');
    });

  function showSubNavPanel(loc) {
    menu.classList.remove('menu--isAboutVisible', 'menu--isNotesVisible');
    menu.dataset.subMenuLocation = loc;
    if (loc === 'info') menu.classList.add('menu--isAboutVisible');
    else if (loc === 'notes') menu.classList.add('menu--isNotesVisible');
  }

  function toggleMainMenu() {
    if (!menu) return;
    const onAbout = menu.classList.contains('menu--isAboutVisible');
    const onNotes = menu.classList.contains('menu--isNotesVisible');

    if (menu.classList.contains('menu--isExpanded') && (onAbout || onNotes)) {
      showSubNavPanel('pages');
      syncMenuOpen();
      return;
    }

    menu.classList.toggle('menu--isExpanded');
    if (!menu.classList.contains('menu--isExpanded')) {
      menu.classList.remove('menu--isAboutVisible', 'menu--isNotesVisible');
      delete menu.dataset.subMenuLocation;
    } else if (!menu.dataset.subMenuLocation) {
      menu.dataset.subMenuLocation = 'pages';
    }
    syncMenuOpen();
  }

  document.addEventListener('click', (e) => {
    if (!e.target.closest('.menu__button')) return;
    e.preventDefault();
    e.stopPropagation();
    toggleMainMenu();
  });

  const pageOverlay = document.getElementById('page-overlay');
  pageOverlay &&
    pageOverlay.addEventListener('click', () => {
      if (!menu.classList.contains('menu--isExpanded')) return;
      menu.classList.remove('menu--isExpanded', 'menu--isAboutVisible', 'menu--isNotesVisible');
      delete menu.dataset.subMenuLocation;
      syncMenuOpen();
    });

  document.querySelectorAll('.subNav__menuItem').forEach((btn) => {
    btn.addEventListener('click', () => {
      if (!menu.classList.contains('menu--isExpanded')) menu.classList.add('menu--isExpanded');
      const loc = btn.dataset.submenuLocation;
      if (loc) showSubNavPanel(loc);
      syncMenuOpen();
    });
  });

  document.querySelectorAll('.subNav a[href]').forEach((a) => {
    a.addEventListener('click', (e) => e.preventDefault());
  });
});
