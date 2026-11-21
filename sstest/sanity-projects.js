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
    s.src = 'sanity-snapshot.js?v=sanity5';
    s.onload = () => resolve(shApplySanitySnapshot(window.SH_SANITY_SNAPSHOT));
    s.onerror = () => resolve(false);
    document.head.appendChild(s);
  });
}

function shSanityBanner(msg) {
  let el = document.getElementById('shSanityBanner');
  if (!el) {
    el = document.createElement('div');
    el.id = 'shSanityBanner';
    el.setAttribute('role', 'status');
    Object.assign(el.style, {
      position: 'fixed',
      bottom: '12px',
      left: '12px',
      right: '12px',
      maxWidth: '520px',
      margin: '0 auto',
      padding: '10px 14px',
      font: '13px/1.35 system-ui,sans-serif',
      background: 'rgba(0,0,0,0.82)',
      color: '#fff',
      zIndex: '99999',
      borderRadius: '6px',
    });
    document.body.appendChild(el);
  }
  el.textContent = msg;
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
    if (location.protocol === 'file:') {
      shSanityBanner(
        'Local file mode: using saved Sanity snapshot. Images are still from Sanity CDN. Run scripts/refresh-sanity-snapshot.sh to refresh.'
      );
    }
    return;
  }

  window.SH_SANITY_SOURCE = 'failed';
  shSanityBanner('Sanity did not load. You need internet. If this persists, run scripts/refresh-sanity-snapshot.sh in SteveStills.');
})();