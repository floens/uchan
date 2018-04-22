(function () {
    'use strict';

    var stylesheets = [];

    function loadAvailableStylesheets() {
        var links = document.head.getElementsByTagName('link');

        for (var i = 0; i < links.length; i++) {
            var link = links[i];

            if (link.getAttribute('rel').indexOf('stylesheet') >= 0) {
                var name = link.getAttribute('data-name');
                if (name) {
                    stylesheets.push([name, link.getAttribute('title')]);
                }
            }
        }
    }

    function setActiveStylesheet(name) {
        var allLinks = document.head.getElementsByTagName('link');

        for (var i = 0; i < allLinks.length; i++) {
            var link = allLinks[i];

            if (link.getAttribute('rel').indexOf('stylesheet') >= 0) {
                var linkName = link.getAttribute('data-name');
                if (linkName) {
                    link.disabled = linkName !== name;
                }
            }
        }

        localStorage.setItem('uchan_active_stylesheet', name);
    }

    function initializeStylesheetSelector() {
        var elem = document.querySelector('.top-bar-right.link-list-right');

        var selector = document.createElement('select');
        for (var i = 0; i < stylesheets.length; i++) {
            var sheet = stylesheets[i];
            var option = document.createElement('option');
            option.value = sheet[0];
            option.innerText = sheet[1];
            selector.appendChild(option);

            if (sheet[0] === localStorage.getItem('uchan_active_stylesheet')) {
                option.selected = true;
            }
        }

        selector.addEventListener('change', function () {
            setActiveStylesheet(selector.options[selector.selectedIndex].value);
        });

        selector.style.marginRight = '0.5em';

        elem.insertBefore(selector, elem.firstChild);

        var text = document.createTextNode('Style: ');
        elem.insertBefore(text, elem.firstChild);
    }

    function initializeActiveStylesheet() {
        var name = localStorage.getItem('uchan_active_stylesheet');
        if (!name) {
            name = stylesheets[0][0]
        }
        setActiveStylesheet(name);
    }

    loadAvailableStylesheets();
    initializeStylesheetSelector();
    initializeActiveStylesheet();

})();
