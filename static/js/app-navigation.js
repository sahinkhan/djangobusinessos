(function () {
  "use strict";

  const safeLinkSelector = "a[data-app-nav]";
  const listFilterSelector = "form[data-list-filter]";
  const listPageSelector = "a[data-list-page]";
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

  function elementsWithin(root, selector) {
    const elements = [];
    if (root instanceof Element && root.matches(selector)) {
      elements.push(root);
    }
    if (root.querySelectorAll) {
      elements.push(...root.querySelectorAll(selector));
    }
    return elements;
  }

  function configureListResults(root) {
    if (!window.htmx) return;

    for (const form of elementsWithin(root, listFilterSelector)) {
      if (form.method.toLowerCase() !== "get") continue;
      const url = new URL(form.action || window.location.href, window.location.href);
      if (url.origin !== window.location.origin) continue;
      url.search = "";
      url.hash = "";
      form.setAttribute("hx-get", url.href);
      form.setAttribute("hx-target", "#list-results");
      form.setAttribute("hx-select", "#list-results");
      form.setAttribute("hx-swap", "outerHTML show:top");
      form.setAttribute("hx-push-url", "true");
      window.htmx.process(form);
    }

    for (const link of elementsWithin(root, listPageSelector)) {
      const url = new URL(link.href, window.location.href);
      if (url.origin !== window.location.origin || link.hasAttribute("download")) continue;
      link.setAttribute("hx-get", url.href);
      link.setAttribute("hx-target", "#list-results");
      link.setAttribute("hx-select", "#list-results");
      link.setAttribute("hx-swap", "outerHTML show:top");
      link.setAttribute("hx-push-url", "true");
      window.htmx.process(link);
    }
  }

  function syncListFiltersFromLocation() {
    const parameters = new URLSearchParams(window.location.search);
    for (const form of document.querySelectorAll(listFilterSelector)) {
      for (const control of form.elements) {
        if (!control.name || control.disabled) continue;
        if (control.type === "submit" || control.type === "button") continue;
        const values = parameters.getAll(control.name);
        if (control.type === "checkbox" || control.type === "radio") {
          control.checked = values.includes(control.value);
        } else if (control.tagName === "SELECT" && control.multiple) {
          for (const option of control.options) {
            option.selected = values.includes(option.value);
          }
        } else {
          control.value = values[0] || "";
        }
      }
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

  function setListResultsLoading(isLoading) {
    for (const shell of document.querySelectorAll("[data-list-results-shell]")) {
      shell.classList.toggle("list-results-loading", isLoading);
      shell.querySelector("[data-list-results-status]")?.setAttribute(
        "aria-hidden",
        isLoading ? "false" : "true",
      );
      shell.querySelector("[data-list-results]")?.setAttribute(
        "aria-busy",
        isLoading ? "true" : "false",
      );
    }
  }

  function finishListResultsLoading() {
    setListResultsLoading(false);
  }

  function fullNavigationFallback(event) {
    finishLoading();
    finishListResultsLoading();
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
    configureListResults(document);
    syncActiveNavigation();
  });

  document.addEventListener("htmx:beforeRequest", function (event) {
    if (event.detail.elt?.closest?.("[data-app-nav]")) {
      document.body.classList.add("app-navigation-loading");
    }
    if (event.detail.elt?.closest?.("[data-list-filter], [data-list-page]")) {
      setListResultsLoading(true);
    }
  });

  document.addEventListener("htmx:afterSwap", function (event) {
    if (event.detail.target?.id === "app-content") {
      finishLoading();
      const content = document.getElementById("app-content");
      configureSafeLinks(content);
      configureListResults(content);
      updateTitle(event.detail.xhr?.responseText);
      syncActiveNavigation();
      window.dispatchEvent(new CustomEvent("app:navigated"));
      content?.focus({ preventScroll: true });
      return;
    }

    if (event.detail.target?.id === "list-results") {
      finishListResultsLoading();
      const results = document.getElementById("list-results");
      configureSafeLinks(results);
      configureListResults(results);
      results?.focus({ preventScroll: true });
    }
  });

  document.addEventListener("htmx:afterRequest", function () {
    finishLoading();
    finishListResultsLoading();
  });
  document.addEventListener("htmx:responseError", fullNavigationFallback);
  document.addEventListener("htmx:sendError", fullNavigationFallback);
  document.addEventListener("htmx:timeout", fullNavigationFallback);
  document.addEventListener("htmx:swapError", fullNavigationFallback);
  document.addEventListener("htmx:targetError", fullNavigationFallback);
  document.addEventListener("htmx:historyRestore", function () {
    finishLoading();
    finishListResultsLoading();
    syncActiveNavigation();
    configureSafeLinks(document.getElementById("app-content"));
    configureListResults(document.getElementById("app-content"));
    syncListFiltersFromLocation();
  });
  window.addEventListener("popstate", function () {
    window.requestAnimationFrame(syncActiveNavigation);
  });
})();
