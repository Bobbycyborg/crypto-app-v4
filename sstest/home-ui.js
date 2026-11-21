/** Home views (locked names): Full-view = list fade; Grid-view = grid. */
document.addEventListener('DOMContentLoaded', async () => {
  if (window.SH_SANITY_READY) await window.SH_SANITY_READY;
  const menu = document.querySelector('.menu');
  const menuBtn = document.querySelector('.menu__button');
  const menuPanelClose = document.querySelector('.menuPanelClose');
  const menuAboutBack = document.querySelector('.menuAboutBack');
  const menuStageTrack = document.getElementById('shMenuStageTrack');
  const viewSwitch = document.querySelector('.view-switch');
  const fullViewBtn = viewSwitch && viewSwitch.querySelector('[data-view="full-view"]');
  const gridViewBtn = viewSwitch && viewSwitch.querySelector('[data-view="grid-view"]');
  const gridRoot = document.getElementById('homeGridGrid');

  const TIERRA_SLUGS = ['charro-pre-23', 'escaramuza', 'charreada-maptia-2015'];
  const TIERRA_TBC = ['Location — TBC', 'Location — TBC', 'Location — TBC', 'Location — TBC'];

  if (gridRoot && window.shHomeGalleryItems) {
    window.shHomeGalleryItems().forEach((item, i) => {
      const article = document.createElement('article');
      article.className = 'gridViewProject';
      const projectAttr = ` data-project="${item.project || 'dungeness'}"`;
      const title = item.title ? `<h3>${item.title}</h3>` : '<h3></h3>';
      const img =
        (window.shImgTag &&
          window.shImgTag(item.src, 'grid', { eager: i === 0, alt: item.title || '' })) ||
        `<img src="${item.src}" alt="${item.title || ''}" loading="lazy">`;
      article.innerHTML = `<a href="#"${projectAttr}><div class="gridViewProject__asset"><div class="responsive-image">${img}</div></div><div class="gridViewProject__description">${title}<h4></h4></div></a>`;
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
    const about = !!(open && menu.classList.contains('menu--isAboutVisible'));
    document.body.classList.toggle('sh-menu-open', !!open);
    document.body.classList.toggle('sh-menu-about', about);
    document.body.classList.remove('sh-menu-notes');
    if (menu) {
      menu.classList.toggle('menu--isExpandedList', !!open && !about);
      if (open && !menu.dataset.subMenuLocation && !about) {
        menu.dataset.subMenuLocation = 'projects';
      }
    }
  }

  function closeMenu() {
    if (!menu) return;
    menu.classList.remove('menu--isExpanded', 'menu--isAboutVisible');
    delete menu.dataset.subMenuLocation;
    syncMenuOpen();
  }

  const MENU_TITLES = {
    projects: 'Selected Work',
    tierra: 'Tierra Adentro',
    archive: 'Archive',
  };

  function setMenuTitle(loc) {
    const el = document.getElementById('shMenuTitleMain');
    if (!el || loc === 'info') return;
    if (MENU_TITLES[loc]) el.textContent = MENU_TITLES[loc];
  }

  function setCol1Active(loc) {
    menu?.querySelectorAll('.subNav__menuItem').forEach((btn) => {
      btn.classList.toggle('is-active', btn.dataset.submenuLocation === loc);
    });
  }

  function showSubNavPanel(loc) {
    if (!menu) return;
    if (loc === 'info') {
      menu.dataset.subMenuLocation = 'info';
      menu.classList.add('menu--isAboutVisible');
      setCol1Active('info');
    } else {
      menu.classList.remove('menu--isAboutVisible');
      menu.dataset.subMenuLocation = loc;
      setCol1Active(loc);
      setMenuTitle(loc);
    }
    syncMenuOpen();
  }

  function menuListItem(title, projectId, muted) {
    if (muted) {
      return `<span class="subNavPages__groupItem subNavPages__groupItem--muted"><span>${title}</span></span>`;
    }
    const id = projectId || '';
    return `<a class="subNavPages__groupItem" href="#" data-project="${id}"><span>${title}</span></a>`;
  }

  function buildMenuLists() {
    const manifests = window.SH_PROJECT_MANIFESTS || {};
    const order = window.SH_PROJECT_ORDER || Object.keys(manifests).sort();
    const projectsRoot = document.getElementById('shMenuProjectsList');
    const tierraRoot = document.getElementById('shMenuTierraList');
    if (projectsRoot) {
      projectsRoot.innerHTML = order
        .map((id) => {
          const m = manifests[id];
          if (!m?.title) return '';
          return menuListItem(m.title, id, false);
        })
        .join('');
    }
    if (tierraRoot) {
      const tierraItems = TIERRA_SLUGS.map((id) => {
        const m = manifests[id];
        const title = m?.title || id;
        return m ? menuListItem(title, id, false) : menuListItem(title, id, true);
      });
      TIERRA_TBC.forEach((t) => tierraItems.push(menuListItem(t, '', true)));
      tierraRoot.innerHTML = tierraItems.join('');
    }
  }

  buildMenuLists();

  function openProjectFromMenu(projectId) {
    if (!projectId || !window.shOpenProject) return;
    closeMenu();
    window.shOpenProject(projectId).catch(() => {});
  }

  function onMenuProjectClick(e) {
    const link = e.target.closest('[data-project]');
    if (!link || link.classList.contains('subNavPages__groupItem--muted')) return;
    const pid = link.dataset.project;
    if (!pid) return;
    e.preventDefault();
    openProjectFromMenu(pid);
  }

  menu?.querySelector('.subNav__container')?.addEventListener('click', onMenuProjectClick);

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

  function toggleMainMenu() {
    if (!menu) return;
    if (menu.classList.contains('menu--isAboutVisible')) {
      showSubNavPanel('projects');
      return;
    }
    menu.classList.toggle('menu--isExpanded');
    if (!menu.classList.contains('menu--isExpanded')) {
      menu.classList.remove('menu--isAboutVisible');
      delete menu.dataset.subMenuLocation;
    } else {
      if (!menu.dataset.subMenuLocation) {
        menu.dataset.subMenuLocation = 'projects';
        setCol1Active('projects');
        setMenuTitle('projects');
      }
      buildMenuLists();
    }
    syncMenuOpen();
  }

  document.addEventListener('click', (e) => {
    if (!e.target.closest('.menu__button')) return;
    e.preventDefault();
    e.stopPropagation();
    toggleMainMenu();
  });

  menuPanelClose?.addEventListener('click', (e) => {
    e.preventDefault();
    closeMenu();
  });

  menuAboutBack?.addEventListener('click', (e) => {
    e.preventDefault();
    showSubNavPanel('projects');
  });

  document.getElementById('page-overlay')?.addEventListener('click', () => {
    if (!menu?.classList.contains('menu--isExpanded')) return;
    closeMenu();
  });

  document.querySelectorAll('.subNav__menuItem').forEach((btn) => {
    btn.addEventListener('click', () => {
      if (!menu.classList.contains('menu--isExpanded')) menu.classList.add('menu--isExpanded');
      const loc = btn.dataset.submenuLocation;
      if (loc) showSubNavPanel(loc);
      if (!menu.dataset.subMenuLocation && loc !== 'info') {
        menu.dataset.subMenuLocation = loc;
      }
      if (!menu.classList.contains('menu--isExpanded')) {
        menu.dataset.subMenuLocation = loc || 'projects';
      }
      syncMenuOpen();
    });
  });
});