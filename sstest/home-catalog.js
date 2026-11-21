window.shHomeGalleryItems = function shHomeGalleryItems() {
  const items = [];
  const manifests = window.SH_PROJECT_MANIFESTS || {};
  const order = window.SH_PROJECT_ORDER || [];
  const ids = order.length ? order : Object.keys(manifests).sort();
  ids.forEach((id) => {
    const m = manifests[id];
    if (!m?.hero || !/^https?:\/\//.test(m.hero)) return;
    items.push({
      src: m.hero,
      project: id,
      title: m.title || id,
    });
  });
  return items;
};

window.shHomeFadeSrcs = function shHomeFadeSrcs() {
  return [...new Set(shHomeGalleryItems().map((item) => item.src))];
};
