(function () {
  "use strict";

  const safeLinkSelector = "a[data-app-nav]";
  const listFilterSelector = "form[data-list-filter]";
  const listPageSelector = "a[data-list-page]";
  let fallbackNavigationStarted = false;

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Tab") return;
    const drawer = document.getElementById("mobile-sidebar");
    if (!drawer?.matches(":modal")) return;
    const controls = [...drawer.querySelectorAll(
      'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), ' +
      'textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
    )].filter((control) => control.tabIndex >= 0 && control.getClientRects().length);
    const first = controls[0];
    const last = controls[controls.length - 1];
    if (!first) {
      event.preventDefault();
      drawer.focus();
    } else if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  });

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
      const url = new URL(link.dataset.appUrl || link.href, window.location.href);
      if (url.origin !== window.location.origin || link.hasAttribute("download")) continue;
      link.dataset.appUrl = url.href;
      const content = document.getElementById("app-content");
      const modulePath = /^\/(parties|catalog|sales|procurement|inventory)\//.test(url.pathname);
      if (modulePath && content?.dataset.companySelected === "false") {
        const companyUrl = new URL(content.dataset.companySelectUrl, window.location.href);
        companyUrl.searchParams.set("next", url.pathname + url.search);
        url.href = companyUrl.href;
      }
      link.href = url.href;
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
      form.setAttribute("hx-swap", "outerHTML show:#app-content:top");
      form.setAttribute("hx-push-url", "true");
      window.htmx.process(form);
    }

    for (const link of elementsWithin(root, listPageSelector)) {
      const url = new URL(link.href, window.location.href);
      if (url.origin !== window.location.origin || link.hasAttribute("download")) continue;
      link.setAttribute("hx-get", url.href);
      link.setAttribute("hx-target", "#list-results");
      link.setAttribute("hx-select", "#list-results");
      link.setAttribute("hx-swap", "outerHTML show:#app-content:top");
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
      link.classList.toggle("is-active", active);
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

  function updateApplicationHeader(responseText) {
    if (!responseText) return;
    const responseDocument = new DOMParser().parseFromString(responseText, "text/html");
    for (const id of ["bos-current-app", "bos-module-menu", "bos-company-context"]) {
      const current = document.getElementById(id);
      const replacement = responseDocument.getElementById(id);
      if (!current || !replacement) continue;
      current.replaceWith(replacement);
      configureSafeLinks(document.getElementById(id));
    }
  }

  function updateControlTail(responseText) {
    if (!responseText) return;
    const responseDocument = new DOMParser().parseFromString(responseText, "text/html");
    const current = document.querySelector("[data-control-tail]");
    const replacement = responseDocument.querySelector("[data-control-tail]");
    if (!current || !replacement) return;
    current.replaceWith(replacement);
    configureListResults(document.querySelector("[data-control-tail]"));
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

  function navigateSameOrigin(path) {
    finishLoading();
    finishListResultsLoading();
    if (fallbackNavigationStarted || !path) return;
    let url;
    try {
      url = new URL(path, window.location.href);
    } catch (_) {
      return;
    }
    if (url.origin !== window.location.origin) return;
    fallbackNavigationStarted = true;
    window.location.assign(url.href);
  }

  function fullNavigationFallback(event) {
    // HTMX's effective GET path includes the parameters serialized from the form.
    // requestConfig.path is only the base action and would discard those parameters.
    navigateSameOrigin(event.detail?.pathInfo?.finalRequestPath);
  }

  document.addEventListener("htmx:historyCacheHit", function (event) {
    // hx-history=false prevents new snapshots, not snapshots left by an older build.
    // Cancel the documented cache-hit event before any old HTML can be restored.
    event.preventDefault();
    navigateSameOrigin(event.detail?.path);
  });

  document.addEventListener("htmx:beforeSwap", function (event) {
    const targetId = event.detail.target?.id;
    if (targetId !== "app-content" && targetId !== "list-results") return;
    const xhr = event.detail.xhr;
    if (!xhr || xhr.status < 200 || xhr.status >= 300) return;
    const response = new DOMParser().parseFromString(
      event.detail.serverResponse || "", "text/html",
    );
    if (response.getElementById("app-content") && response.getElementById(targetId)) return;
    // A successful redirect may have left the authenticated fragment contract.
    // Follow the final response URL, never infer authentication from a URL name.
    event.detail.shouldSwap = false;
    event.preventDefault();
    navigateSameOrigin(xhr.responseURL);
  });

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
      configureSafeLinks(document);
      configureListResults(content);
      updateTitle(event.detail.xhr?.responseText);
      updateApplicationHeader(event.detail.xhr?.responseText);
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
      updateControlTail(event.detail.xhr?.responseText);
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
