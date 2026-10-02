// Shared by the browser renderer and frame-selection tests.
(function (root) {
  function source(clip, localTime, manifest) {
    const asset = manifest[clip.id];
    if (!asset || asset.frames < 1 || asset.fps <= 0) throw new Error(`Missing clip: ${clip.id}`);
    const time = (clip.offset || 0) + Math.max(0, localTime - (clip.start || 0)) * (clip.rate ?? 1);
    const frame = Math.min(asset.frames - 1, Math.max(0, Math.floor(time * asset.fps + 1e-7)));
    return `${asset.dir}/${String(frame).padStart(5, "0")}.jpg`;
  }
  if (typeof module !== "undefined") module.exports = { source };
  else root.clipFrameSource = source;
})(typeof window !== "undefined" ? window : globalThis);
