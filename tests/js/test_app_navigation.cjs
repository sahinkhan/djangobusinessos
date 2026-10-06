const assert = require("node:assert/strict");
const test = require("node:test");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

function harness({drawer = null, activeElement = null} = {}) {
  const listeners = new Map();
  const navigations = [];
  const document = {
    addEventListener: (name, fn) => {
      assert.equal(listeners.has(name), false, `duplicate ${name} listener`);
      listeners.set(name, fn);
    },
    getElementById: () => drawer,
    activeElement,
    querySelectorAll: () => [],
    body: {classList: {remove() {}}},
  };
  class DOMParser {
    parseFromString(html) {
      return {getElementById: (id) => html.includes(`id="${id}"`) ? {} : null};
    }
  }
  const window = {
    location: {href: "http://localhost:8000/inventory/movements/", origin: "http://localhost:8000",
      assign: (url) => navigations.push(url)},
    addEventListener() {},
  };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../../static/js/app-navigation.js"), "utf8"),
    {document, window, URL, URLSearchParams, DOMParser});
  return {navigations, emit(name, detail) {
    const event = {detail, ...detail, cancelled: false, preventDefault() {this.cancelled = true;}};
    listeners.get(name)(event);
    return event;
  }};
}

test("legacy cache hits are cancelled before server-authorized full navigation", () => {
  const h = harness();
  assert.equal(h.emit("htmx:historyCacheHit", {path: "/parties/?q=A_ONLY"}).cancelled, true);
  assert.deepEqual(h.navigations, ["http://localhost:8000/parties/?q=A_ONLY"]);
});

for (const target of ["app-content", "list-results"]) {
  test(`successful response missing ${target} uses final redirect URL, not request URL`, () => {
    const h = harness();
    const event = h.emit("htmx:beforeSwap", {target: {id: target}, shouldSwap: true,
      serverResponse: '<main>Sign in</main>',
      xhr: {status: 200, responseURL: "http://localhost:8000/login/?next=/parties/"}});
    assert.equal(event.cancelled, true);
    assert.equal(event.detail.shouldSwap, false);
    assert.deepEqual(h.navigations, ["http://localhost:8000/login/?next=/parties/"]);
  });
}

test("valid authenticated fragments keep the swap contract", () => {
  const h = harness();
  const event = h.emit("htmx:beforeSwap", {target: {id: "list-results"},
    serverResponse: '<div id="app-content"><div id="list-results"></div></div>',
    xhr: {status: 200, responseURL: "http://localhost:8000/parties/"}});
  assert.equal(event.cancelled, false);
  assert.deepEqual(h.navigations, []);
});

for (const eventName of ["htmx:responseError", "htmx:sendError", "htmx:timeout", "htmx:swapError"]) {
  for (const query of ["q=A_ONLY+Movement1", "type=receipt", "q=A_ONLY+Movement1&type=receipt&status=posted&page=2"]) {
    test(`${eventName} retains effective GET parameters: ${query}`, () => {
      const h = harness();
      h.emit(eventName, {requestConfig: {path: "/inventory/movements/"},
        pathInfo: {finalRequestPath: `/inventory/movements/?${query}`}});
      assert.deepEqual(h.navigations, [`http://localhost:8000/inventory/movements/?${query}`]);
    });
  }
}

test("foreign-origin history/error/redirect paths cannot trigger a navigation", () => {
  const h = harness();
  const e = h.emit("htmx:historyCacheHit", {path: "https://example.test/stale"});
  assert.equal(e.cancelled, true);
  h.emit("htmx:sendError", {pathInfo: {finalRequestPath: "https://example.test/failure"}});
  h.emit("htmx:beforeSwap", {target: {id: "app-content"}, serverResponse: "no fragment",
    xhr: {status: 200, responseURL: "https://example.test/login"}});
  assert.deepEqual(h.navigations, []);
});

test("duplicate failure events cause exactly one full navigation", () => {
  const h = harness();
  const detail = {pathInfo: {finalRequestPath: "/parties/?q=A_ONLY"}};
  h.emit("htmx:responseError", detail);
  h.emit("htmx:swapError", detail);
  assert.equal(h.navigations.length, 1);
});

for (const backwards of [false, true]) {
  test(`mobile modal wraps ${backwards ? "Shift+Tab" : "Tab"}`, () => {
    let focused;
    const first = {tabIndex: 0, getClientRects: () => [1], focus: () => {focused = "first";}};
    const last = {tabIndex: 0, getClientRects: () => [1], focus: () => {focused = "last";}};
    const hidden = {tabIndex: 0, getClientRects: () => [], focus: () => assert.fail("hidden focus")};
    const drawer = {matches: () => true, querySelectorAll: () => [first, last, hidden]};
    const h = harness({drawer, activeElement: backwards ? first : last});
    const e = h.emit("keydown", {key: "Tab", shiftKey: backwards});
    assert.equal(e.cancelled, true);
    assert.equal(focused, backwards ? "last" : "first");
  });
}

test("closed/desktop drawer leaves normal keyboard navigation untouched", () => {
  const h = harness({drawer: {matches: () => false}});
  assert.equal(h.emit("keydown", {key: "Tab"}).cancelled, false);
});
