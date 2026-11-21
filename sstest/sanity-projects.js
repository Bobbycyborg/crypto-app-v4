function shApplySanitySnapshot(snap) {
  if (!snap?.manifests || !Object.keys(snap.manifests).length) return false;
  window.SH_PROJECT_MANIFESTS = snap.manifests;
  window.SH_PROJECT_ORDER = snap.order || Object.keys(snap.manifests);
  return true;
}

function shLoadSanitySnapshot() {
  return new Promise((resolve) => {
    if (window.SH_SANITY_SNAPSHOT) {
      resolve(shApplySanitySnapshot(window.SH_SANITY_SNAPSHOT));
      return;
    }
    const s = document.createElement('script');
    s.src = 'sanity-snapshot.js?v=sanity6';
    s.onload = () => resolve(shApplySanitySnapshot(window.SH_SANITY_SNAPSHOT));
    s.onerror = () => resolve(false);
    document.head.appendChild(s);
  });
}

window.SH_SANITY_READY = (async () => {
  const query =
    '*[_type == "project" && defined(title)] | order(orderRank asc) { _id, title, "slug": slug.current, text, link, perRow, "hero": hero.asset->url, "images": images[].asset->url }';
  const url =
    'https://kkt6i72t.api.sanity.io/v2024-01-01/data/query/production?query=' +
    encodeURIComponent(query);

  let live = false;
  try {
    const res = await fetch(url);
    if (res.ok) {
      const data = await res.json();
      const manifests = {};
      const order = [];
      for (const project of data.result || []) {
        const images = (project.images || []).filter(Boolean);
        const id =
          project.slug ||
          String(project.title || '')
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-|-$/g, '') ||
          project._id;
        if (!id || !images.length) continue;
        manifests[id] = {
          id,
          title: project.title || id,
          hero: project.hero || images[0],
          images,
          text: project.text || '',
          link: project.link || '',
          perRow: project.perRow || 0,
        };
        order.push(id);
      }
      if (order.length) {
        window.SH_PROJECT_MANIFESTS = manifests;
        window.SH_PROJECT_ORDER = order;
        live = true;
      }
    }
  } catch (_) {
    /* file:// or network */
  }

  if (live) {
    window.SH_SANITY_SOURCE = 'live';
    return;
  }

  const snapOk = await shLoadSanitySnapshot();
  if (snapOk) {
    window.SH_SANITY_SOURCE = 'snapshot';
    return;
  }

  window.SH_SANITY_SOURCE = 'failed';
  console.error('Sanity did not load — check internet or run scripts/refresh-sanity-snapshot.sh');
})();