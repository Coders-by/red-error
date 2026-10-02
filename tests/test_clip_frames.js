const test = require("node:test");
const assert = require("node:assert/strict");
const { source } = require("../web/clip-frames.js");
const manifest = { take: { dir: "video/take", frames: 120, fps: 24 } };

test("starts on frame zero, holds the end and never loops on a dissolve", () => {
  assert.equal(source({ id: "take" }, 0, manifest), "video/take/00000.jpg");
  assert.equal(source({ id: "take" }, 1 / 24, manifest), "video/take/00001.jpg");
  assert.equal(source({ id: "take" }, 5.9, manifest), "video/take/00119.jpg");
});
test("delayed action holds first frame before the dialogue ends", () => {
  const clip = { id: "take", start: 10.68 };
  assert.equal(source(clip, 3, manifest), "video/take/00000.jpg");
  assert.equal(source(clip, 10.68 + 1 / 24, manifest), "video/take/00001.jpg");
});
test("a returning shot resumes the handover end instead of replaying it", () => {
  assert.equal(source({ id: "take", offset: 4 }, 0, manifest), "video/take/00096.jpg");
  assert.equal(source({ id: "take", offset: 4, rate: 2 }, .5, manifest), "video/take/00119.jpg");
});
test("unknown media fails explicitly", () => {
  assert.throws(() => source({ id: "absent" }, 0, manifest), /Missing clip/);
});
