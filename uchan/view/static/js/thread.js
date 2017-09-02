(function () {
    'use strict';

    var bindRefnos = function () {
        var formText = document.querySelector('.post-form [name=comment]');

        var refnos = document.querySelectorAll('a.refno');
        for (var i = 0; i < refnos.length; i++) {
            var refno = refnos[i];
            refno.addEventListener('click', function (event) {
                event.preventDefault();
                var refnoText = this.textContent;
                formText.value += '>>' + refnoText.substring(refnoText.indexOf('#') + 1).trim() + '\n';
            });
        }
    };

    var listenToFileCount = function () {
        var maxFilesAllowed = window.pageDetails['fileMax'];

        var elements = document.querySelectorAll('.post-form input[type=file]');
        for (var i = 0; i < elements.length; i++) {
            var element = elements[i];

            var check = function () {
                var overLimit = this.files.length > maxFilesAllowed;
                var submit = this.parentElement.parentElement.querySelector('input[type=submit]');
                submit.disabled = overLimit;
            };

            element.addEventListener('change', check);
            check.call(element);
        }
    };

    if (window.pageDetails['mode'] === 'thread') {
        bindRefnos();
    }

    if (window.pageDetails['filePostingEnabled']) {
        listenToFileCount();
    }
})();
