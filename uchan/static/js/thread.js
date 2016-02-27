(function() {
    'use strict';

    var bindRefnos = function() {
        var formText = document.querySelector('.post-form [name=comment]');

        var refnos = document.querySelectorAll('a.refno');
        for (var i = 0; i < refnos.length; i++) {
            var refno = refnos[i];
            refno.addEventListener('click', function(event) {
                event.preventDefault();
                var refnoText = this.textContent;
                formText.value += '>>' + refnoText.substring(refnoText.indexOf('#') + 1).trim() + '\n';
            });
        }
    };

    var highlightHash = function() {
        var currentlyHighlightedPosts = document.querySelectorAll('.post.highlight');
        if (currentlyHighlightedPosts) {
            for (var i = 0; i < currentlyHighlightedPosts.length; i++) {
                currentlyHighlightedPosts[i].classList.remove('highlight');
            }
        }

        var hash = location.hash;
        var postRefno = parseInt(hash.substring(hash.indexOf('#p') + 2).trim());
        if (postRefno) {
            var toHighlight = document.querySelector('#p' + postRefno + '.post');
            if (toHighlight) {
                toHighlight.classList.add('highlight');
            }
        }
    };

    bindRefnos();

    highlightHash();

    window.addEventListener('hashchange', highlightHash, false);
})();
