// One build can be served on several hosts. Keep registration hidden unless allowed.
(() => {
  const registration = document.getElementById('site-registration');
  if (!registration) return;
  const normalize = value => value.trim().toLowerCase().replace(/\.$/, '');
  const hostname = normalize(window.location.hostname);
  try {
    const domains = JSON.parse(registration.dataset.domains);
    const suffixes = JSON.parse(registration.dataset.domainSuffixes);
    const exact = domains.some(value => hostname === normalize(value));
    const suffix = suffixes.some(value => {
      const domain = normalize(value);
      return domain && (hostname === domain || hostname.endsWith('.' + domain));
    });
    registration.hidden = !(hostname && (exact || suffix));
  } catch {
    // Invalid configuration must never expose registration on an unrelated host.
    registration.hidden = true;
  }
})();
