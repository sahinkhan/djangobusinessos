(function () {
  "use strict";

  const safeLinkSelector = "a[data-app-nav]";
  let fallbackNavigationStarted = false;

  function linksWithin(root) {
    const links = [];
    if (root instanceof Element && root.matches(safeLinkSelector)) {
      links.push(root);
    }
    if (root.querySelectorAll) {
      links.push(...root.querySelectorAll(safeLinkSelector));
    }
    return links;
  }

  function configureSafeLinks(root) {
    if (!window.htmx) return;
    for (const link of linksWithin(root)) {
      const url = new URL(link.href, window.location.href);
      if (url.origin !== window.location.origin || link.hasAttribute("download")) continue;
      link.setAttribute("hx-get", url.href);
      link.setAttribute("hx-target", "#app-content");
      link.setAttribute("hx-select", "#app-content");
      link.setAttribute("hx-swap", "outerHTML show:top");
      link.setAttribute("hx-push-url", "true");
      window.htmx.process(link);
    }
  }

  function syncActiveNavigation() {
    const path = window.location.pathname;
    for (const link of document.querySelectorAll("[data-nav-root]")) {
      const root = link.dataset.navRoot;
      const active = root === "/" ? path === "/" : path.startsWith(root);
      link.classList.toggle("nav-item-active", active);
      if (active) {
        link.setAttribute("aria-current", "page");
      } else {
        link.removeAttribute("aria-current");
      }
    }
  }

  function updateTitle(responseText) {
    if (!responseText) return;
    const responseDocument = new DOMParser().parseFromString(responseText, "text/html");
    const title = responseDocument.querySelector("title")?.textContent?.trim();
    if (title) document.title = title;
  }

  function finishLoading() {
    document.body.classList.remove("app-navigation-loading");
  }

  function fullNavigationFallback(event) {
    finishLoading();
    if (fallbackNavigationStarted) return;
    const path = event.detail?.requestConfig?.path;
    if (!path) return;
    const url = new URL(path, window.location.href);
    if (url.origin !== window.location.origin) return;
    fallbackNavigationStarted = true;
    window.location.assign(url.href);
  }

  document.addEventListener("DOMContentLoaded", function () {
    configureSafeLinks(document);
    syncActiveNavigation();
  });

  document.addEventListener("htmx:beforeRequest", function (event) {
    if (event.detail.elt?.closest?.("[data-app-nav]")) {
      document.body.classList.add("app-navigation-loading");
    }
  });

  document.addEventListener("htmx:afterSwap", function (event) {
    if (event.detail.target?.id !== "app-content") return;
    finishLoading();
    const content = document.getElementById("app-content");
    configureSafeLinks(content);
    updateTitle(event.detail.xhr?.responseText);
    syncActiveNavigation();
    window.dispatchEvent(new CustomEvent("app:navigated"));
    content?.focus({ preventScroll: true });
  });

  document.addEventListener("htmx:afterRequest", finishLoading);
  document.addEventListener("htmx:responseError", fullNavigationFallback);
  document.addEventListener("htmx:sendError", fullNavigationFallback);
  document.addEventListener("htmx:timeout", fullNavigationFallback);
  document.addEventListener("htmx:swapError", fullNavigationFallback);
  document.addEventListener("htmx:targetError", fullNavigationFallback);
  document.addEventListener("htmx:historyRestore", function () {
    finishLoading();
    syncActiveNavigation();
    configureSafeLinks(document.getElementById("app-content"));
  });
  window.addEventListener("popstate", function () {
    window.requestAnimationFrame(syncActiveNavigation);
  });
})();
