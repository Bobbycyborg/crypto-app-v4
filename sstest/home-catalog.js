window.shHomeGalleryItems = function shHomeGalleryItems() {
  const items = [];
  const scroller = document.getElementById('shProjectScroller');
  const dungenessSrc = scroller?.querySelector('.asset img[src]')?.getAttribute('src');
  if (dungenessSrc) {
    items.push({ src: dungenessSrc, project: 'dungeness', title: 'Dungeness' });
  }

  const manifests = window.SH_PROJECT_MANIFESTS || {};
  Object.keys(manifests)
    .sort()
    .forEach((id) => {
      const m = manifests[id];
      if (!m?.hero) return;
      items.push({
        src: `img/${id}/${m.hero}`,
        project: id,
        title: m.title || id,
      });
    });

  return items;
};

window.shHomeFadeSrcs = function shHomeFadeSrcs() {
  return [...new Set(shHomeGalleryItems().map((item) => item.src))];
};
