(function () {
  "use strict";

  let stylesheets = [];

  function loadAvailableStylesheets() {
    var links = document.head.getElementsByTagName("link");

    for (var i = 0; i < links.length; i++) {
      var link = links[i];

      if (link.getAttribute("rel").indexOf("stylesheet") >= 0) {
        var name = link.getAttribute("data-theme");
        if (name) {
          stylesheets.push([name, link.getAttribute("title")]);
        }
      }
    }
  }

  function setActiveStylesheet(name) {
    var allLinks = document.head.getElementsByTagName("link");

    for (var i = 0; i < allLinks.length; i++) {
      var link = allLinks[i];

      if (link.getAttribute("rel").indexOf("stylesheet") >= 0) {
        var linkName = link.getAttribute("data-theme");
        if (linkName) {
          link.disabled = linkName !== name;
        }
      }
    }

    localStorage.setItem("uchan_active_stylesheet", name);
  }

  function initializeStylesheetSelector() {
    var elem = document.querySelector(".top-bar-right.link-list-right");

    var selector = document.createElement("select");
    selector.id = "theme-selector";

    for (var i = 0; i < stylesheets.length; i++) {
      var sheet = stylesheets[i];
      var option = document.createElement("option");
      option.value = sheet[0];
      option.innerText = sheet[1];
      selector.appendChild(option);
    }

    selector.style.marginRight = "0.5em";

    elem.insertBefore(selector, elem.firstChild);

    var text = document.createTextNode("Style: ");
    elem.insertBefore(text, elem.firstChild);

    setTimeout(function () {
      selector = document.querySelector("#theme-selector");
      selector.value = localStorage.getItem("uchan_active_stylesheet");
      console.log(selector);

      selector.addEventListener("change", function (e) {
        setActiveStylesheet(selector.options[selector.selectedIndex].value);
      });
    }, 0);
  }

  function initializeActiveStylesheet() {
    var name = localStorage.getItem("uchan_active_stylesheet");
    if (!name) {
      name = stylesheets[0][0];
    }
    setActiveStylesheet(name);
  }

  var bindRefnos = function () {
    var formText = document.querySelector(".post-form [name=comment]");

    var refnos = document.querySelectorAll("a.refno");
    for (var i = 0; i < refnos.length; i++) {
      var refno = refnos[i];
      refno.addEventListener("click", function (event) {
        event.preventDefault();
        var refnoText = this.textContent;
        formText.value +=
          ">>" + refnoText.substring(refnoText.indexOf("#") + 1).trim() + "\n";
      });
    }
  };

  var listenToFileCount = function () {
    var maxFilesAllowed = window.pageDetails["fileMax"];

    var elements = document.querySelectorAll(".post-form input[type=file]");
    for (var i = 0; i < elements.length; i++) {
      var element = elements[i];

      var check = function () {
        var overLimit = this.files.length > maxFilesAllowed;
        var submit = this.parentElement.parentElement.querySelector(
          "input[type=submit]"
        );
        submit.disabled = overLimit;
      };

      element.addEventListener("change", check);
      check.call(element);
    }
  };

  // FIXME: broken because of issues with the addEventListener,
  // and issues with disabling the correct stylesheets on page load.
  // loadAvailableStylesheets();
  // initializeStylesheetSelector();
  // initializeActiveStylesheet();

  if (window.pageDetails["mode"] === "thread") {
    bindRefnos();
  }

  if (window.pageDetails["filePostingEnabled"]) {
    listenToFileCount();
  }
})();
