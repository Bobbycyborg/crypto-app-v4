document.addEventListener('DOMContentLoaded', () => {
  const menu = document.querySelector('.menu');
  const menuBtn = document.querySelector('.menu__button');
  const indexToggle = document.querySelector('.indexToggle');
  const listBtn = indexToggle && indexToggle.querySelector('a[aria-label="Featured Projects"]');
  const gridBtn = indexToggle && indexToggle.querySelector('a[aria-label="All Projects"]');
  const gridRoot = document.getElementById('homeGridGrid');

  const images = [
    'img/011.jpg',
    'img/15554201594_76a210c28c_h.jpg',
    'img/21tg.jpeg',
    'img/25964819690_1e5c16a845_b.jpg',
    'img/45e16cd1270e43cbecc850c85fd688e8.jpg',
    'img/5964610613_e9c1c4c127_b.jpg',
    'img/KyleThompson_metalmagazine_7.jpg',
    'img/original.jpg',
    'img/tumblr_o1ad8krEfs1ukenxjo1_1280.jpg',
    'img/tumblr_o2jq6sS0V91th0flao1_1280.jpg'
  ];

  if (gridRoot) {
    images.forEach((src) => {
      const article = document.createElement('article');
      article.className = 'gridViewProject';
      article.innerHTML = `<a href="#"><div class="gridViewProject__asset"><div class="responsive-image"><img src="${src}" alt="" loading="lazy"></div></div><div class="gridViewProject__description"><h3></h3><h4></h4></div></a>`;
      gridRoot.appendChild(article);
    });
  }

  document.body.dataset.homeView = 'list';
  if (indexToggle) indexToggle.dataset.activeIndex = 'list';

  function setView(view) {
    document.body.dataset.homeView = view;
    if (indexToggle) indexToggle.dataset.activeIndex = view === 'grid' ? 'grid' : 'list';
  }

  listBtn &&
    listBtn.addEventListener('click', (e) => {
      e.preventDefault();
      setView('list');
    });

  gridBtn &&
    gridBtn.addEventListener('click', (e) => {
      e.preventDefault();
      setView('grid');
    });

  menuBtn &&
    menuBtn.addEventListener('click', () => {
      menu.classList.toggle('menu--isExpanded');
      if (!menu.classList.contains('menu--isExpanded')) {
        menu.classList.remove('menu--isAboutVisible', 'menu--isNotesVisible');
        delete menu.dataset.subMenuLocation;
      } else if (!menu.dataset.subMenuLocation) {
        menu.dataset.subMenuLocation = 'pages';
      }
    });

  document.querySelectorAll('.subNav__menuItem').forEach((btn) => {
    btn.addEventListener('click', () => {
      if (!menu.classList.contains('menu--isExpanded')) menu.classList.add('menu--isExpanded');
      menu.classList.remove('menu--isAboutVisible', 'menu--isNotesVisible');
      const loc = btn.dataset.submenuLocation;
      if (loc) menu.dataset.subMenuLocation = loc;
      if (loc === 'info') menu.classList.add('menu--isAboutVisible');
      if (loc === 'notes') menu.classList.add('menu--isNotesVisible');
    });
  });

  document.querySelectorAll('.subNav a[href]').forEach((a) => {
    a.addEventListener('click', (e) => e.preventDefault());
  });
});
