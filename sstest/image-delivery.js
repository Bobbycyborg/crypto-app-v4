window.SH_SANITY_ONLY = true;

window.SH_IMAGE = {
  q: 80,
  fit: 'max',
  gallery: { widths: [1200, 2000, 2800], sizes: '100vw' },
  overview: { widths: [600, 1200], sizes: '220px' },
  tray: { widths: [600, 1200], sizes: '(max-width: 719px) 96px, 140px' },
  grid: { widths: [600, 1200], sizes: '(min-width: 720px) 25vw, 50vw' },
};

window.shIsSanityImage = function shIsSanityImage(url) {
  return typeof url === 'string' && url.includes('cdn.sanity.io/images/');
};

function shImageBase(url) {
  const u = new URL(url, window.location.href);
  u.search = '';
  return u;
}

function shImageDims(url) {
  const match = String(url).match(/-(\d+)x(\d+)\.[a-z0-9]+/i);
  if (!match) return null;
  return { width: match[1], height: match[2] };
}

function shSizedUrl(url, width) {
  const u = shImageBase(url);
  u.searchParams.set('w', String(width));
  u.searchParams.set('auto', 'format');
  u.searchParams.set('q', String(window.SH_IMAGE.q));
  u.searchParams.set('fit', window.SH_IMAGE.fit);
  return u.toString();
}

window.shImgTag = function shImgTag(url, kind, opts) {
  if (!window.shIsSanityImage(url)) return '';
  const spec = window.SH_IMAGE[kind] || window.SH_IMAGE.gallery;
  const dims = shImageDims(url);
  const srcset = spec.widths.map((width) => `${shSizedUrl(url, width)} ${width}w`).join(', ');
  const wh = dims ? ` width="${dims.width}" height="${dims.height}"` : '';
  const loading = opts && opts.eager ? 'eager' : 'lazy';
  const alt = opts && opts.alt ? String(opts.alt).replace(/"/g, '&quot;') : '';
  return `<img src="${shSizedUrl(url, spec.widths[0])}" srcset="${srcset}" sizes="${spec.sizes}"${wh} alt="${alt}" decoding="async" loading="${loading}">`;
};
