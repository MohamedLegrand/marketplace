/* Marketplace admin - bascule d'affichage des champs mot de passe (icone oeil). */
(function () {
  "use strict";

  var EYE =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
    '<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>';

  var EYE_OFF =
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
    '<path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/>' +
    '<path d="M10.73 5.08A10.4 10.4 0 0 1 12 5c7 0 10 7 10 7a13.2 13.2 0 0 1-1.67 2.68"/>' +
    '<path d="M6.61 6.61A13.5 13.5 0 0 0 2 12s3 7 10 7a9.7 9.7 0 0 0 5.39-1.61"/>' +
    '<line x1="2" x2="22" y1="2" y2="22"/></svg>';

  function enhance(input) {
    if (input.dataset.pwEnhanced) {
      return;
    }
    input.dataset.pwEnhanced = "1";

    var host = input.closest(".field-wrap, .pw-field");
    if (!host) {
      host = document.createElement("span");
      host.className = "pw-field";
      input.parentNode.insertBefore(host, input);
      host.appendChild(input);
    }

    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "pw-toggle";
    btn.setAttribute("aria-label", "Afficher le mot de passe");
    btn.innerHTML = EYE;
    host.appendChild(btn);

    btn.addEventListener("click", function () {
      var reveal = input.type === "password";
      input.type = reveal ? "text" : "password";
      btn.innerHTML = reveal ? EYE_OFF : EYE;
      btn.setAttribute(
        "aria-label",
        reveal ? "Masquer le mot de passe" : "Afficher le mot de passe"
      );
      input.focus();
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll('input[type="password"]').forEach(enhance);
  });
})();
